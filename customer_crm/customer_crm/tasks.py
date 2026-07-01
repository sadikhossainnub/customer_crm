import frappe
from frappe.utils import today, add_days, get_url

def send_daily_followup_reminders():
	"""Send reminders 1 day before follow-up date"""
	tomorrow = add_days(today(), 1)
	
	pending_todos = frappe.get_all("ToDo", 
		filters={
			"reference_type": "Customer Call",
			"status": "Open",
			"date": tomorrow
		},
		fields=["name", "description", "owner", "reference_name"]
	)
	
	for todo in pending_todos:
		call = frappe.get_doc("Customer Call", todo.reference_name)
		
		frappe.sendmail(
			recipients=[todo.owner],
			subject=f"Reminder: Follow-up due tomorrow - {call.customer}",
			message=f"""This is a reminder that you have a follow-up call due tomorrow.
			
Customer: {call.customer}
Phone: {call.phone or 'Not available'}
Follow-up Date: {tomorrow}
Previous Notes: {call.notes or 'No notes'}

View Call: {get_url()}/app/customer-call/{call.name}
Mark Complete: {get_url()}/app/todo/{todo.name}"""
		)


def notify_unmatched_auto_calls():
	"""Notify System Managers about auto-logged calls that may need review (today)"""
	unmatched_count = frappe.db.count("Customer Call", {
		"is_auto_logged": 1,
		"customer": ["is", "not set"],
		"call_date": today()
	})
	if unmatched_count:
		managers = frappe.get_all("Has Role", filters={"role": "System Manager"}, fields=["parent"])
		for m in managers:
			frappe.publish_realtime(
				"msgprint",
				{"message": f"⚠️ {unmatched_count} auto-logged call(s) today have no customer match and need review."},
				user=m.parent
			)