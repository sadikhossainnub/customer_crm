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