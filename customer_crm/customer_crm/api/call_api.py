import frappe

@frappe.whitelist()
def get_call_stats():
	"""Get call statistics for dashboard"""
	today = frappe.utils.today()
	
	stats = {
		"today_calls": frappe.db.count("Customer Call", {"call_date": today}),
		"pending_followups": frappe.db.count("ToDo", {
			"reference_type": "Customer Call",
			"status": "Open",
			"date": ["<=", today]
		}),
		"interested_calls": frappe.db.count("Customer Call", {
			"call_date": today,
			"call_outcome": "Interested"
		})
	}
	
	return stats

@frappe.whitelist()
def get_agent_calls(agent=None, date=None):
	"""Get calls for specific agent and date"""
	if not agent:
		agent = frappe.session.user
	if not date:
		date = frappe.utils.today()
	
	calls = frappe.get_all("Customer Call",
		filters={"agent": agent, "call_date": date},
		fields=["name", "customer", "call_time", "call_outcome", "next_follow_up_date"],
		order_by="call_time desc"
	)
	
	return calls