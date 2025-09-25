import frappe
from frappe import _

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
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
			"label": _("Customer"),
			"fieldname": "customer",
			"fieldtype": "Link",
			"options": "Customer",
			"width": 150
		},
		{
			"label": _("Agent"),
			"fieldname": "agent",
			"fieldtype": "Link",
			"options": "User",
			"width": 120
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
		}
	]

def get_data(filters):
	conditions = ""
	if filters.get("from_date"):
		conditions += f" AND call_date >= '{filters.get('from_date')}'"
	if filters.get("to_date"):
		conditions += f" AND call_date <= '{filters.get('to_date')}'"
	if filters.get("agent"):
		conditions += f" AND agent = '{filters.get('agent')}'"
	
	return frappe.db.sql(f"""
		SELECT 
			call_date,
			customer,
			agent,
			call_outcome,
			call_duration,
			next_follow_up_date
		FROM `tabCustomer Call`
		WHERE 1=1 {conditions}
		ORDER BY call_date DESC, call_time DESC
	""", as_dict=1)