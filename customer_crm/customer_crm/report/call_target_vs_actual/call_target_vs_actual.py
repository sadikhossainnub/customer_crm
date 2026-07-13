import frappe
from frappe import _
from frappe.utils import today, getdate, date_diff


def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	chart = get_chart(data)
	summary = get_summary(data)
	return columns, data, None, chart, summary


def get_columns():
	return [
		{
			"label": _("Agent"),
			"fieldname": "agent",
			"fieldtype": "Link",
			"options": "User",
			"width": 180
		},
		{
			"label": _("Agent Name"),
			"fieldname": "agent_name",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"label": _("Period"),
			"fieldname": "period",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"label": _("Target Calls"),
			"fieldname": "target_calls",
			"fieldtype": "Int",
			"width": 110
		},
		{
			"label": _("Actual Calls"),
			"fieldname": "actual_calls",
			"fieldtype": "Int",
			"width": 110
		},
		{
			"label": _("Remaining"),
			"fieldname": "remaining",
			"fieldtype": "Int",
			"width": 100
		},
		{
			"label": _("Achievement %"),
			"fieldname": "achievement_pct",
			"fieldtype": "Percent",
			"width": 120
		},
		{
			"label": _("Target Interested"),
			"fieldname": "target_interested",
			"fieldtype": "Int",
			"width": 130
		},
		{
			"label": _("Actual Interested"),
			"fieldname": "actual_interested",
			"fieldtype": "Int",
			"width": 130
		},
		{
			"label": _("Interested %"),
			"fieldname": "interested_pct",
			"fieldtype": "Percent",
			"width": 110
		},
		{
			"label": _("Status"),
			"fieldname": "status",
			"fieldtype": "Data",
			"width": 110
		}
	]


def get_data(filters):
	from_date = filters.get("from_date") or today()
	to_date   = filters.get("to_date") or today()
	agent_filter = filters.get("agent")

	# --- fetch all active targets for the date range ---
	target_conditions = "from_date <= %(to_date)s AND to_date >= %(from_date)s"
	target_args = {"from_date": from_date, "to_date": to_date}
	if agent_filter:
		target_conditions += " AND agent = %(agent)s"
		target_args["agent"] = agent_filter

	targets = frappe.db.sql(f"""
		SELECT
			agent,
			target_period,
			from_date,
			to_date,
			COALESCE(daily_call_target, 0)       AS daily_call_target,
			COALESCE(weekly_call_target, 0)      AS weekly_call_target,
			COALESCE(daily_interested_target, 0) AS daily_interested_target,
			COALESCE(weekly_interested_target, 0) AS weekly_interested_target
		FROM `tabAgent Call Target`
		WHERE {target_conditions}
		ORDER BY agent, from_date
	""", target_args, as_dict=True)

	if not targets:
		# If no targets defined, show all agents with actual calls only
		return _get_actuals_only(from_date, to_date, agent_filter)

	rows = []
	for t in targets:
		agent_name = frappe.db.get_value("User", t.agent, "full_name") or t.agent

		# Overlap period = max(from_date, filter_from) .. min(to_date, filter_to)
		period_start = max(getdate(t.from_date), getdate(from_date))
		period_end   = min(getdate(t.to_date),   getdate(to_date))
		days_in_period = date_diff(period_end, period_start) + 1

		# Pick target based on period type
		if t.target_period == "Daily":
			call_target = t.daily_call_target * days_in_period
			int_target  = t.daily_interested_target * days_in_period
		elif t.target_period == "Weekly":
			weeks = max(days_in_period / 7, 1)
			call_target = round(t.weekly_call_target * weeks)
			int_target  = round(t.weekly_interested_target * weeks)
		else:  # Monthly — treat the stored weekly * 4 as proxy, or use daily*days
			call_target = t.daily_call_target * days_in_period
			int_target  = t.daily_interested_target * days_in_period

		# Actual calls in overlap period
		actual_calls, actual_interested = _get_actual_counts(
			t.agent, period_start, period_end
		)

		remaining       = max(call_target - actual_calls, 0)
		achievement_pct = round((actual_calls / call_target * 100), 1) if call_target else 0
		interested_pct  = round((actual_interested / int_target * 100), 1) if int_target else 0

		if achievement_pct >= 100:
			status = "✅ On Target"
		elif achievement_pct >= 75:
			status = "🟡 Near Target"
		elif achievement_pct >= 50:
			status = "🟠 Below Target"
		else:
			status = "🔴 Critical"

		rows.append({
			"agent":            t.agent,
			"agent_name":       agent_name,
			"period":           f"{frappe.utils.formatdate(period_start)} – {frappe.utils.formatdate(period_end)}",
			"target_calls":     call_target,
			"actual_calls":     actual_calls,
			"remaining":        remaining,
			"achievement_pct":  achievement_pct,
			"target_interested": int_target,
			"actual_interested": actual_interested,
			"interested_pct":   interested_pct,
			"status":           status,
		})

	return rows


def _get_actual_counts(agent, from_date, to_date):
	"""Return (total_calls, interested_calls) for an agent in the date range."""
	result = frappe.db.sql("""
		SELECT
			COUNT(*) AS total,
			SUM(CASE WHEN call_outcome = 'Interested' THEN 1 ELSE 0 END) AS interested
		FROM `tabCustomer Call`
		WHERE agent = %s AND call_date BETWEEN %s AND %s
	""", (agent, from_date, to_date), as_dict=True)
	if result:
		return int(result[0].total or 0), int(result[0].interested or 0)
	return 0, 0


def _get_actuals_only(from_date, to_date, agent_filter=None):
	"""Fallback when no targets defined: list all agents with actuals only."""
	conditions = "call_date BETWEEN %(from_date)s AND %(to_date)s"
	args = {"from_date": from_date, "to_date": to_date}
	if agent_filter:
		conditions += " AND agent = %(agent)s"
		args["agent"] = agent_filter

	rows = frappe.db.sql(f"""
		SELECT
			agent,
			COUNT(*) AS actual_calls,
			SUM(CASE WHEN call_outcome = 'Interested' THEN 1 ELSE 0 END) AS actual_interested
		FROM `tabCustomer Call`
		WHERE {conditions}
		GROUP BY agent
		ORDER BY actual_calls DESC
	""", args, as_dict=True)

	data = []
	for r in rows:
		data.append({
			"agent":            r.agent,
			"agent_name":       frappe.db.get_value("User", r.agent, "full_name") or r.agent,
			"period":           f"{frappe.utils.formatdate(from_date)} – {frappe.utils.formatdate(to_date)}",
			"target_calls":     0,
			"actual_calls":     int(r.actual_calls or 0),
			"remaining":        0,
			"achievement_pct":  0,
			"target_interested": 0,
			"actual_interested": int(r.actual_interested or 0),
			"interested_pct":   0,
			"status":           "⚫ No Target Set",
		})
	return data


def get_chart(data):
	if not data:
		return None
	labels = [r.get("agent_name") or r.get("agent") for r in data]
	return {
		"data": {
			"labels": labels,
			"datasets": [
				{"name": _("Target Calls"),  "values": [r["target_calls"]  for r in data]},
				{"name": _("Actual Calls"),  "values": [r["actual_calls"]  for r in data]},
			]
		},
		"type": "bar",
		"colors": ["#5470C6", "#91CC75"],
		"barOptions": {"stacked": False}
	}


def get_summary(data):
	if not data:
		return []
	total_target = sum(r["target_calls"]  for r in data)
	total_actual = sum(r["actual_calls"]  for r in data)
	overall_pct  = round(total_actual / total_target * 100, 1) if total_target else 0
	on_target    = sum(1 for r in data if r["achievement_pct"] >= 100)

	return [
		{"label": _("Total Target Calls"),  "value": total_target, "indicator": "blue"},
		{"label": _("Total Actual Calls"),  "value": total_actual, "indicator": "green"},
		{"label": _("Overall Achievement"), "value": f"{overall_pct}%", "indicator": "green" if overall_pct >= 100 else "orange"},
		{"label": _("Agents On Target"),    "value": f"{on_target}/{len(data)}", "indicator": "green" if on_target == len(data) else "orange"},
	]
