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


def find_customer_by_phone(phone):
	"""Lookup Customer by phone number — checks Customer.mobile_no and Contact Phone child table"""
	if not phone:
		return None
	phone = phone.strip()
	# Check Customer's direct mobile number
	customer = frappe.db.get_value("Customer", {"mobile_no": phone})
	if customer:
		return customer
	# Check Contact Phone linked to Customer via Dynamic Link
	contact = frappe.db.sql("""
		SELECT dl.link_name FROM `tabDynamic Link` dl
		JOIN `tabContact Phone` cp ON cp.parent = dl.parent
		WHERE dl.link_doctype = 'Customer' AND cp.phone = %s
		LIMIT 1
	""", phone)
	return contact[0][0] if contact else None


@frappe.whitelist(allow_guest=False)
def log_call_from_pbx(from_number, to, duration, uniqueid, agent_ext=None):
	"""Whitelisted endpoint called by Asterisk on call hangup (h extension).
	Matches caller/callee to a Customer and creates a Customer Call record."""
	settings = frappe.get_single("Telephony Settings")
	if not settings.enable_auto_logging:
		return

	customer = find_customer_by_phone(from_number) or find_customer_by_phone(to)
	agent_user = None
	if agent_ext:
		agent_user = frappe.db.get_value("User", {"phone": agent_ext}, "name")
	agent_user = agent_user or frappe.session.user

	# Duplicate guard — skip if this Asterisk unique ID already logged
	if frappe.db.exists("Customer Call", {"call_id": uniqueid}):
		return

	if customer:
		doc = frappe.get_doc({
			"doctype": "Customer Call",
			"customer": customer,
			"agent": agent_user,
			"call_id": uniqueid,
			"call_duration": int(duration or 0),
			"call_status": "Completed" if int(duration or 0) > 0 else "Missed",
			"call_direction": "Inbound",
			"is_auto_logged": 1,
			"conversation_summary": "Auto-logged from PBX - pending agent notes"
		}).insert(ignore_permissions=True)
		frappe.db.commit()
		return doc.name
	else:
		frappe.publish_realtime("unmatched_call", {"number": from_number})


@frappe.whitelist(allow_guest=False)
def notify_incoming_call(from_number, agent_ext):
	"""Called by Asterisk on incoming call ring event.
	Pushes a realtime notification to the matched agent's browser for screen pop."""
	customer = find_customer_by_phone(from_number)
	agent_user = frappe.db.get_value("User", {"phone": agent_ext}, "name")
	info = {"number": from_number, "customer": customer}
	if agent_user:
		frappe.publish_realtime("incoming_call_popup", info, user=agent_user)