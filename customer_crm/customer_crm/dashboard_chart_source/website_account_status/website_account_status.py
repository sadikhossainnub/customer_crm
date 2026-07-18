import frappe

@frappe.whitelist()
def get(chart_name=None, chart=None, filters=None, **kwargs):
	if isinstance(filters, str):
		import json
		try:
			filters = json.loads(filters)
		except Exception:
			filters = {}
	elif not filters:
		filters = {}

	customer = filters.get("customer") or filters.get("name")

	if customer:
		has_user = frappe.db.exists("Portal User", {"parent": customer, "parenttype": "Customer"})
		labels = ["Has Web Account", "No Web Account"]
		values = [1, 0] if has_user else [0, 1]
	else:
		total_customers = frappe.db.count("Customer", {"disabled": 0})
		portal_customers = frappe.db.sql("""
			SELECT COUNT(DISTINCT parent)
			FROM `tabPortal User`
			WHERE parenttype = 'Customer'
		""")[0][0] or 0
		no_portal_customers = max(0, total_customers - portal_customers)
		
		labels = ["Has Web Account", "No Web Account"]
		values = [portal_customers, no_portal_customers]

	return {
		"labels": labels,
		"datasets": [{"values": values}]
	}
