import frappe

no_cache = 1

def get_context(context):
	# Write debug log
	with open("/home/sayed/frappe-bench/apps/customer_crm/customer_crm/www/debug_call_center.txt", "w") as f:
		f.write(f"User: {frappe.session.user}\n")
		f.write(f"Today: {frappe.utils.today()}\n")
		f.write(f"Session: {frappe.session}\n")

	# Redirect Guest users to login page
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=/call-center"
		raise frappe.Redirect

	context.title = "Call Center Dashboard"
	context.current_user = frappe.session.user
	today = frappe.utils.today()
	
	# 1. Get today's call target details for the logged-in agent
	target = frappe.db.sql("""
		SELECT name, daily_call_target, daily_interested_target
		FROM `tabAgent Call Target`
		WHERE agent = %s AND from_date <= %s AND to_date >= %s
		LIMIT 1
	""", (frappe.session.user, today, today), as_dict=True)
	
	context.daily_call_target = (target[0].daily_call_target or 0) if target else 0
	context.daily_interested_target = (target[0].daily_interested_target or 0) if target else 0

	# Count calls made today by this agent
	count = frappe.db.sql("""
		SELECT COUNT(*) as cnt FROM `tabCustomer Call`
		WHERE agent = %s AND call_date = %s
	""", (frappe.session.user, today), as_dict=True)
	context.calls_made_today = count[0].cnt if count else 0

	# Calculate percentage progress
	if context.daily_call_target > 0:
		context.call_target_progress = min(100, int((context.calls_made_today / context.daily_call_target) * 100))
	else:
		context.call_target_progress = 0

	# 2. Get customers assigned to the current user (active assignments covering today)
	assigned_customers = frappe.db.sql("""
		SELECT DISTINCT cac.customer, cac.customer_name, cac.from_date, cac.to_date
		FROM `tabCustomer Assignment` ca
		JOIN `tabCustomer Assignment Agent` caa ON caa.parent = ca.name
		JOIN `tabCustomer Assignment Customer` cac ON cac.parent = ca.name
		WHERE ca.is_active = 1
		  AND caa.agent = %s
		  AND (caa.from_date IS NULL OR caa.from_date <= %s)
		  AND (caa.to_date IS NULL OR caa.to_date >= %s)
		  AND (cac.from_date IS NULL OR cac.from_date <= %s)
		  AND (cac.to_date IS NULL OR cac.to_date >= %s)
		ORDER BY cac.customer_name ASC
	""", (frappe.session.user, today, today, today, today), as_dict=True) or []

	# Find which assigned customers have already been called today by this agent
	called_today_customers = frappe.db.sql("""
		SELECT DISTINCT customer FROM `tabCustomer Call`
		WHERE agent = %s AND call_date = %s
	""", (frappe.session.user, today), as_dict=True)
	called_set = {c.customer for c in called_today_customers}

	# Add status and build lists
	context.assigned_customers = []
	context.pending_calls = []
	
	for item in assigned_customers:
		is_called = item.customer in called_set
		item_copy = dict(item)
		item_copy["status"] = "Called" if is_called else "Pending"
		context.assigned_customers.append(item_copy)
		if not is_called:
			context.pending_calls.append(item_copy)
	
	# 3. Get 10 most recent calls overall by the logged-in agent
	context.recent_calls = frappe.db.sql("""
		SELECT name, customer, agent, call_outcome, call_time, call_date
		FROM `tabCustomer Call`
		WHERE agent = %s
		ORDER BY call_date DESC, call_time DESC
		LIMIT 10
	""", (frappe.session.user,), as_dict=True) or []
	
	return context