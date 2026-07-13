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


def send_today_followup_summary():
	"""Send a daily summarized email and in-app notification to each agent listing their follow-ups due today"""
	current_date = today()
	
	pending_todos = frappe.get_all("ToDo",
		filters={
			"reference_type": "Customer Call",
			"status": "Open",
			"date": current_date
		},
		fields=["name", "description", "owner", "reference_name"]
	)
	
	agent_todos = {}
	for todo in pending_todos:
		owner = todo.owner
		if not owner:
			continue
		if owner not in agent_todos:
			agent_todos[owner] = []
		agent_todos[owner].append(todo)
		
	for agent, todos in agent_todos.items():
		todo_items_html = []
		todo_items_text = []
		
		for index, todo in enumerate(todos, start=1):
			call = frappe.get_doc("Customer Call", todo.reference_name)
			
			called_phone = 'Not available'
			if call.phone:
				for p in call.phone:
					if p.is_called:
						called_phone = p.phone
						break
			
			view_url = f"{get_url()}/app/customer-call/{call.name}"
			
			todo_items_text.append(
				f"{index}. Customer: {call.customer}\n"
				f"   Phone: {called_phone}\n"
				f"   View Call: {view_url}\n"
			)
			
			todo_items_html.append(
				f"<li>"
				f"<strong>Customer:</strong> {call.customer}<br>"
				f"<strong>Phone:</strong> {called_phone}<br>"
				f"<a href='{view_url}'>View Call Details</a>"
				f"</li><br>"
			)
			
		email_message = f"""
		<h3>Daily Follow-up Reminder</h3>
		<p>You have <strong>{len(todos)}</strong> customer follow-ups due today ({current_date}):</p>
		<ul>
			{"".join(todo_items_html)}
		</ul>
		"""
		
		frappe.sendmail(
			recipients=[agent],
			subject=f"Today's Follow-up List - {current_date}",
			message="\n".join(todo_items_text),
			html=email_message
		)
		
		frappe.publish_realtime(
			event="today_followups_summary",
			message={
				"count": len(todos),
				"date": current_date,
				"msg": f"You have {len(todos)} customer follow-ups scheduled for today!"
			},
			user=agent
		)