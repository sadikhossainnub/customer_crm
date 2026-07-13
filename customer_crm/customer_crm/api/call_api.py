import frappe
from frappe.utils import today as _today, getdate, date_diff


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
def get_target_vs_actual(from_date=None, to_date=None, agent=None):
	"""Get target vs actual call counts for all agents (or specific agent).
	Used by the Call Dashboard to show progress bars."""
	from_date = from_date or _today()
	to_date   = to_date   or _today()

	# Get active targets for the period
	target_conditions = "from_date <= %(to_date)s AND to_date >= %(from_date)s"
	target_args = {"from_date": from_date, "to_date": to_date}
	if agent:
		target_conditions += " AND agent = %(agent)s"
		target_args["agent"] = agent

	targets = frappe.db.sql(f"""
		SELECT
			agent,
			target_period,
			from_date, to_date,
			COALESCE(daily_call_target, 0)        AS daily_call_target,
			COALESCE(weekly_call_target, 0)       AS weekly_call_target,
			COALESCE(daily_interested_target, 0)  AS daily_interested_target,
			COALESCE(weekly_interested_target, 0) AS weekly_interested_target
		FROM `tabAgent Call Target`
		WHERE {target_conditions}
		ORDER BY agent, from_date
	""", target_args, as_dict=True)

	result = []
	for t in targets:
		period_start = max(getdate(t.from_date), getdate(from_date))
		period_end   = min(getdate(t.to_date),   getdate(to_date))
		days         = date_diff(period_end, period_start) + 1

		if t.target_period == "Daily":
			call_target = t.daily_call_target * days
			int_target  = t.daily_interested_target * days
		elif t.target_period == "Weekly":
			weeks = max(days / 7, 1)
			call_target = round(t.weekly_call_target * weeks)
			int_target  = round(t.weekly_interested_target * weeks)
		else:
			call_target = t.daily_call_target * days
			int_target  = t.daily_interested_target * days

		actual = frappe.db.sql("""
			SELECT
				COUNT(*) AS total,
				SUM(CASE WHEN call_outcome = 'Interested' THEN 1 ELSE 0 END) AS interested
			FROM `tabCustomer Call`
			WHERE agent = %s AND call_date BETWEEN %s AND %s
		""", (t.agent, period_start, period_end), as_dict=True)[0]

		actual_calls     = int(actual.total or 0)
		actual_interested = int(actual.interested or 0)
		achievement_pct  = round(actual_calls / call_target * 100, 1) if call_target else 0
		interested_pct   = round(actual_interested / int_target * 100, 1) if int_target else 0

		result.append({
			"agent":             t.agent,
			"agent_name":        frappe.db.get_value("User", t.agent, "full_name") or t.agent,
			"call_target":       call_target,
			"actual_calls":      actual_calls,
			"remaining":         max(call_target - actual_calls, 0),
			"achievement_pct":   min(achievement_pct, 100),
			"int_target":        int_target,
			"actual_interested": actual_interested,
			"interested_pct":    min(interested_pct, 100),
		})

	return result

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
		fields=["name", "call_date", "call_time", "agent", "call_outcome", "conversation_summary"],
		order_by="call_date desc, call_time desc"
	)

	for call in calls:
		if call.agent:
			call.agent_name = frappe.db.get_value("User", call.agent, "full_name") or call.agent
		else:
			call.agent_name = "System"

	return calls


@frappe.whitelist()
def get_last_call_detail(customer, current_call=None):
	if not customer:
		return ""
	
	filters = {"customer": customer}
	if current_call:
		filters["name"] = ["!=", current_call]
		
	last_call = frappe.get_all("Customer Call",
		filters=filters,
		fields=["call_date", "call_time", "agent"],
		order_by="call_date desc, call_time desc",
		limit=1
	)
	
	if not last_call:
		return "No previous calls"
		
	call = last_call[0]
	
	# Format date
	call_date = call.call_date
	if isinstance(call_date, str):
		call_date = frappe.utils.getdate(call_date)
		
	def get_day_suffix(day):
		if 11 <= day <= 13:
			return "th"
		return {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
		
	day_suffix = get_day_suffix(call_date.day)
	date_str = f"{call_date.day}{day_suffix} {call_date.strftime('%B')} {call_date.year}"
	
	# Format time
	time_str = ""
	if call.call_time:
		t = call.call_time
		if isinstance(t, str):
			try:
				import datetime
				dt = datetime.datetime.strptime(t, "%H:%M:%S")
				time_str = dt.strftime("%I:%M %p")
			except Exception:
				time_str = t
		else:
			import datetime
			dt = (datetime.datetime.min + t)
			time_str = dt.strftime("%I:%M %p")
			
	# Format agent
	agent_name = "System"
	if call.agent:
		agent_name = frappe.db.get_value("User", call.agent, "full_name") or call.agent
		
	# Calculate days
	days_elapsed = frappe.utils.date_diff(frappe.utils.today(), call_date)
	
	# Construct string
	detail = f"{date_str}"
	if time_str:
		detail += f" {time_str}"
	detail += f", Agent: {agent_name}, ( {days_elapsed} Days)"
	
	return detail


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
			"conversation_summary": "Auto-logged from PBX"
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