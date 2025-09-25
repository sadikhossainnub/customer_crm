import frappe

def after_install():
	"""Setup basic data after app installation"""
	create_custom_fields()
	setup_permissions()

def create_custom_fields():
	"""Add custom fields to Customer doctype for better integration"""
	if not frappe.db.exists("Custom Field", {"dt": "Customer", "fieldname": "last_call_date"}):
		frappe.get_doc({
			"doctype": "Custom Field",
			"dt": "Customer",
			"label": "Last Call Date",
			"fieldname": "last_call_date",
			"fieldtype": "Date",
			"insert_after": "customer_name",
			"read_only": 1
		}).insert()
	
	if not frappe.db.exists("Custom Field", {"dt": "Customer", "fieldname": "next_follow_up"}):
		frappe.get_doc({
			"doctype": "Custom Field",
			"dt": "Customer",
			"label": "Next Follow-up",
			"fieldname": "next_follow_up",
			"fieldtype": "Date",
			"insert_after": "last_call_date",
			"read_only": 1
		}).insert()

def setup_permissions():
	"""Setup basic permissions for Sales User role"""
	pass