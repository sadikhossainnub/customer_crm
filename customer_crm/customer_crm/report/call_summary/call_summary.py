import frappe
from frappe import _
from frappe.utils import today, getdate, date_diff


def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data    = get_data(filters)
	return columns, data


def get_columns():
	return [
		{
			"label": _("Date"),
			"fieldname": "call_date",
			"fieldtype": "Date",
			"width": 100
		},
		{
			"label": _("Agent"),
			"fieldname": "agent",
			"fieldtype": "Link",
			"options": "User",
			"width": 140
		},
		{
			"label": _("Customer"),
			"fieldname": "customer",
			"fieldtype": "Link",
			"options": "Customer",
			"width": 150
		},
		{
			"label": _("Call Outcome"),
			"fieldname": "call_outcome",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"label": _("Duration"),
			"fieldname": "call_duration",
			"fieldtype": "Duration",
			"width": 100
		},
		{
			"label": _("Next Follow-up"),
			"fieldname": "next_follow_up_date",
			"fieldtype": "Date",
			"width": 120
		},
		{
			"label": _("Daily Target"),
			"fieldname": "daily_target",
			"fieldtype": "Int",
			"width": 110
		},
		{
			"label": _("Calls That Day"),
			"fieldname": "calls_that_day",
			"fieldtype": "Int",
			"width": 120
		},
		{
			"label": _("Day Achievement %"),
			"fieldname": "day_achievement_pct",
			"fieldtype": "Percent",
			"width": 130
		},
	]


def get_data(filters):
	conditions = ""
	if filters.get("from_date"):
		conditions += " AND cc.call_date >= %(from_date)s"
	if filters.get("to_date"):
		conditions += " AND cc.call_date <= %(to_date)s"
	if filters.get("agent"):
		conditions += " AND cc.agent = %(agent)s"
	if filters.get("call_outcome"):
		conditions += " AND cc.call_outcome = %(call_outcome)s"

	calls = frappe.db.sql(f"""
		SELECT
			cc.call_date,
			cc.agent,
			cc.customer,
			cc.call_outcome,
			cc.call_duration,
			cc.next_follow_up_date
		FROM `tabCustomer Call` cc
		WHERE 1=1 {conditions}
		ORDER BY cc.call_date DESC, cc.call_time DESC
	""", filters, as_dict=True)

	# Build a cache: (agent, date) -> (daily_target, calls_that_day)
	_target_cache = {}
	_count_cache  = {}

	rows = []
	for c in calls:
		key = (c.agent, str(c.call_date))

		if key not in _count_cache:
			_count_cache[key] = frappe.db.count(
				"Customer Call",
				{"agent": c.agent, "call_date": c.call_date}
			)

		if key not in _target_cache:
			_target_cache[key] = _get_daily_target(c.agent, c.call_date)

		daily_target     = _target_cache[key]
		calls_that_day   = _count_cache[key]
		achievement_pct  = round(calls_that_day / daily_target * 100, 1) if daily_target else 0

		rows.append({
			"call_date":          c.call_date,
			"agent":              c.agent,
			"customer":           c.customer,
			"call_outcome":       c.call_outcome,
			"call_duration":      c.call_duration,
			"next_follow_up_date": c.next_follow_up_date,
			"daily_target":       daily_target,
			"calls_that_day":     calls_that_day,
			"day_achievement_pct": achievement_pct,
		})

	return rows


def _get_daily_target(agent, call_date):
	"""Return the daily call target for an agent on a given date."""
	target = frappe.db.sql("""
		SELECT daily_call_target, weekly_call_target, target_period
		FROM `tabAgent Call Target`
		WHERE agent = %s AND from_date <= %s AND to_date >= %s
		ORDER BY from_date DESC
		LIMIT 1
	""", (agent, call_date, call_date), as_dict=True)

	if not target:
		return 0
	t = target[0]
	if t.target_period == "Weekly":
		return round((t.weekly_call_target or 0) / 7)
	return t.daily_call_target or 0