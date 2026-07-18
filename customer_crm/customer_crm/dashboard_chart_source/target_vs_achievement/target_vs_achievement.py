import frappe
from frappe.utils import today, get_last_day

@frappe.whitelist()
def get(chart_name=None, chart=None, filters=None, **kwargs):
	if isinstance(filters, str):
		import json
		filters = json.loads(filters)
	filters = filters or {}

	# Default dates to current month if not specified
	if not filters.get("from_date"):
		filters["from_date"] = today()[:-2] + "01"
	if not filters.get("to_date"):
		filters["to_date"] = str(get_last_day(today()))

	from_date = filters["from_date"]
	to_date = filters["to_date"]

	# Restrict non-System Manager users to their own data
	is_system_manager = "System Manager" in frappe.get_roles(frappe.session.user)
	agent_filter = filters.get("agent")

	if not is_system_manager:
		agent_filter = frappe.session.user

	# Build WHERE clause
	agent_cond = ""
	target_args = {"from_date": from_date, "to_date": to_date}
	actual_args = {"from_date": from_date, "to_date": to_date}

	if agent_filter:
		agent_cond = "AND agent = %(agent)s"
		target_args["agent"] = agent_filter
		actual_args["agent"] = agent_filter

	# Fetch targets: daily_call_target × working days in range
	targets = frappe.db.sql(f"""
		SELECT
			agent,
			SUM(COALESCE(daily_call_target, 0)) AS call_target
		FROM `tabAgent Call Target`
		WHERE from_date <= %(to_date)s AND to_date >= %(from_date)s
		  {agent_cond}
		GROUP BY agent
		ORDER BY agent
	""", target_args, as_dict=True)

	# Fetch actuals: COUNT DISTINCT customers called per agent in range
	actuals = frappe.db.sql(f"""
		SELECT
			agent,
			COUNT(DISTINCT customer) AS unique_customers_called
		FROM `tabCustomer Call`
		WHERE call_date BETWEEN %(from_date)s AND %(to_date)s
		  {agent_cond}
		GROUP BY agent
		ORDER BY agent
	""", actual_args, as_dict=True)

	# Map agent → name
	def get_name(agent):
		return frappe.db.get_value("User", agent, "full_name") or agent

	# Merge targets and actuals
	target_map = {t.agent: int(t.call_target or 0) for t in targets}
	actual_map = {a.agent: int(a.unique_customers_called or 0) for a in actuals}

	all_agents = sorted(set(list(target_map.keys()) + list(actual_map.keys())))

	labels = [get_name(a) for a in all_agents]
	target_values = [target_map.get(a, 0) for a in all_agents]
	actual_values = [actual_map.get(a, 0) for a in all_agents]

	return {
		"labels": labels if labels else ["No Data"],
		"datasets": [
			{"name": "Target (Customers)", "values": target_values if target_values else [0]},
			{"name": "Achieved (Unique Customers Called)", "values": actual_values if actual_values else [0]}
		]
	}
