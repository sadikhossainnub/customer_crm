import frappe

def get_context(context):
	context.title = "Call Center Dashboard"
	
	# Get pending follow-ups for today
	context.pending_calls = frappe.get_all("ToDo", 
		filters={
			"reference_type": "Customer Call",
			"status": "Open",
			"date": ["<=", frappe.utils.today()]
		},
		fields=["name", "description", "date", "owner", "reference_name"]
	)
	
	# Get recent calls
	context.recent_calls = frappe.get_all("Customer Call",
		filters={"call_date": frappe.utils.today()},
		fields=["name", "customer", "agent", "call_outcome", "call_time"],
		order_by="call_time desc",
		limit=10
	)
	
	return context