import frappe

@frappe.whitelist()
def get(chart_name=None, chart=None, filters=None, **kwargs):
	if isinstance(filters, str):
		import json
		filters = json.loads(filters)
	filters = filters or {}
	customer = filters.get("customer") or filters.get("name")
	
	if not customer:
		return {"labels": [], "datasets": []}
		
	addr_count = frappe.db.count("Dynamic Link", {"link_doctype": "Customer", "link_name": customer, "parenttype": "Address"})
	contact_count = frappe.db.count("Dynamic Link", {"link_doctype": "Customer", "link_name": customer, "parenttype": "Contact"})
	
	return {
		"labels": ["Addresses", "Contacts"],
		"datasets": [{"values": [addr_count, contact_count]}]
	}
