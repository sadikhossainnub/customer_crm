import frappe
from frappe import _

def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data    = get_data(filters)
	chart   = get_chart(data)
	summary = get_report_summary(data)
	return columns, data, None, chart, summary


def get_columns():
	return [
		{
			"label": _("Call ID"),
			"fieldname": "name",
			"fieldtype": "Link",
			"options": "Customer Call",
			"width": 140
		},
		{
			"label": _("Call Date"),
			"fieldname": "call_date",
			"fieldtype": "Date",
			"width": 100
		},
		{
			"label": _("Call Time"),
			"fieldname": "call_time",
			"fieldtype": "Time",
			"width": 90
		},
		{
			"label": _("Customer ID"),
			"fieldname": "customer",
			"fieldtype": "Link",
			"options": "Customer",
			"width": 140
		},
		{
			"label": _("Customer Name"),
			"fieldname": "customer_name",
			"fieldtype": "Data",
			"width": 160
		},
		{
			"label": _("Phone Number"),
			"fieldname": "phone_number",
			"fieldtype": "Data",
			"width": 130
		},
		{
			"label": _("Agent"),
			"fieldname": "agent",
			"fieldtype": "Link",
			"options": "User",
			"width": 140
		},
		{
			"label": _("Direction"),
			"fieldname": "call_direction",
			"fieldtype": "Data",
			"width": 110
		},
		{
			"label": _("Status"),
			"fieldname": "call_status",
			"fieldtype": "Data",
			"width": 110
		},
		{
			"label": _("Duration"),
			"fieldname": "call_duration",
			"fieldtype": "Duration",
			"width": 100
		},
		{
			"label": _("Call Outcome"),
			"fieldname": "call_outcome",
			"fieldtype": "Link",
			"options": "Call Outcome",
			"width": 130
		},
		{
			"label": _("Next Follow-up"),
			"fieldname": "next_follow_up_date",
			"fieldtype": "Date",
			"width": 120
		},
		{
			"label": _("Auto Logged"),
			"fieldname": "is_auto_logged",
			"fieldtype": "Check",
			"width": 100
		},
		{
			"label": _("Summary"),
			"fieldname": "conversation_summary",
			"fieldtype": "Small Text",
			"width": 220
		}
	]


def get_data(filters):
	conditions = []
	values = {}

	if filters.get("from_date"):
		conditions.append("cc.call_date >= %(from_date)s")
		values["from_date"] = filters["from_date"]
	if filters.get("to_date"):
		conditions.append("cc.call_date <= %(to_date)s")
		values["to_date"] = filters["to_date"]
	if filters.get("customer"):
		conditions.append("cc.customer = %(customer)s")
		values["customer"] = filters["customer"]
	if filters.get("agent"):
		conditions.append("cc.agent = %(agent)s")
		values["agent"] = filters["agent"]
	if filters.get("call_direction"):
		conditions.append("cc.call_direction = %(call_direction)s")
		values["call_direction"] = filters["call_direction"]
	if filters.get("call_status"):
		conditions.append("cc.call_status = %(call_status)s")
		values["call_status"] = filters["call_status"]
	if filters.get("call_outcome"):
		conditions.append("cc.call_outcome = %(call_outcome)s")
		values["call_outcome"] = filters["call_outcome"]
	if filters.get("phone"):
		conditions.append("EXISTS (SELECT 1 FROM `tabCustomer Call Phone` ccp WHERE ccp.parent = cc.name AND ccp.phone LIKE %(phone)s)")
		values["phone"] = f"%{filters['phone']}%"

	where_clause = " AND ".join(conditions)
	if where_clause:
		where_clause = "WHERE " + where_clause
	else:
		where_clause = ""

	calls = frappe.db.sql(f"""
		SELECT
			cc.name,
			cc.call_date,
			cc.call_time,
			cc.customer,
			cc.customer_name,
			cc.agent,
			cc.call_direction,
			cc.call_status,
			cc.call_duration,
			cc.call_outcome,
			cc.next_follow_up_date,
			cc.is_auto_logged,
			cc.conversation_summary
		FROM `tabCustomer Call` cc
		{where_clause}
		ORDER BY cc.call_date DESC, cc.call_time DESC
	""", values, as_dict=True)

	data = []
	for c in calls:
		# Fetch primary phone number called from child table
		phone = frappe.db.sql("""
			SELECT phone FROM `tabCustomer Call Phone`
			WHERE parent = %s AND is_called = 1
			LIMIT 1
		""", (c.name,))
		if not phone:
			phone = frappe.db.sql("""
				SELECT phone FROM `tabCustomer Call Phone`
				WHERE parent = %s LIMIT 1
			""", (c.name,))
		
		c["phone_number"] = phone[0][0] if phone else ""
		data.append(c)

	return data


def get_chart(data):
	if not data:
		return None

	status_counts = {}
	for d in data:
		st = d.get("call_status") or "Unspecified"
		status_counts[st] = status_counts.get(st, 0) + 1

	labels = list(status_counts.keys())
	values = [status_counts[l] for l in labels]

	return {
		"data": {
			"labels": labels,
			"datasets": [{"name": _("Call Status Breakdown"), "values": values}]
		},
		"type": "donut",
		"colors": ["#28a745", "#007bff", "#dc3545", "#ffc107", "#6c757d"]
	}


def get_report_summary(data):
	if not data:
		return []

	total_calls = len(data)
	completed = sum(1 for d in data if d.get("call_status") == "Completed")
	missed = sum(1 for d in data if d.get("call_status") == "Missed")
	interested = sum(1 for d in data if d.get("call_outcome") == "Interested")
	total_duration_sec = sum(int(d.get("call_duration") or 0) for d in data)

	dur_min = total_duration_sec // 60
	dur_sec = total_duration_sec % 60
	dur_str = f"{dur_min}m {dur_sec}s" if dur_min else f"{dur_sec}s"

	return [
		{
			"value": total_calls,
			"indicator": "Blue",
			"label": _("Total Calls"),
			"datatype": "Int",
		},
		{
			"value": completed,
			"indicator": "Green",
			"label": _("Completed Calls"),
			"datatype": "Int",
		},
		{
			"value": missed,
			"indicator": "Red",
			"label": _("Missed Calls"),
			"datatype": "Int",
		},
		{
			"value": interested,
			"indicator": "Green",
			"label": _("Interested Outcomes"),
			"datatype": "Int",
		},
		{
			"value": dur_str,
			"indicator": "Orange",
			"label": _("Total Duration"),
			"datatype": "Data",
		},
	]
