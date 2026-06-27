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

@frappe.whitelist()
def get_customer_phones(customer):
	if not customer:
		return []

	phones = []
	seen = set()

	def add_phone(phone, label, contact_person=""):
		if not phone:
			return
		clean_phone = phone.strip()
		if clean_phone and clean_phone not in seen:
			seen.add(clean_phone)
			phones.append({
				"phone": clean_phone,
				"label": label,
				"contact_person": contact_person
			})

	# 1. Customer's direct number
	customer_doc = frappe.get_doc("Customer", customer)
	if customer_doc.mobile_no:
		add_phone(customer_doc.mobile_no, "Customer Mobile", customer)

	# 2. Contacts' numbers
	contacts = frappe.get_all("Contact", filters=[
		["Dynamic Link", "link_doctype", "=", "Customer"],
		["Dynamic Link", "link_name", "=", customer],
		["status", "=", "Active"]
	], fields=["name", "full_name", "mobile_no", "phone"])

	for contact in contacts:
		name = contact.full_name or contact.name
		if contact.mobile_no:
			add_phone(contact.mobile_no, "Contact Mobile", name)
		if contact.phone:
			add_phone(contact.phone, "Contact Phone", name)
		
		# Child table numbers
		contact_doc = frappe.get_doc("Contact", contact.name)
		if hasattr(contact_doc, "phone_nos"):
			for p in contact_doc.phone_nos:
				if p.phone:
					label = "Contact Phone"
					if p.is_primary_mobile_no:
						label = "Contact Primary Mobile"
					elif p.is_primary_phone:
						label = "Contact Primary Phone"
					add_phone(p.phone, label, name)

	return phones

@frappe.whitelist()
def get_customer_history(customer, current_call=None):
	if not customer:
		return []

	filters = {"customer": customer}
	if current_call:
		filters["name"] = ["!=", current_call]

	calls = frappe.get_all("Customer Call",
		filters=filters,
		fields=["name", "call_date", "call_time", "agent", "call_outcome", "conversation_summary", "notes"],
		order_by="call_date desc, call_time desc"
	)

	for call in calls:
		if call.agent:
			call.agent_name = frappe.db.get_value("User", call.agent, "full_name") or call.agent
		else:
			call.agent_name = "System"

	return calls