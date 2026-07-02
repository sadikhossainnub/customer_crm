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
		
	has_user = frappe.db.exists("Portal User", {"parent": customer})
	labels = ["Has Web Account", "No Web Account"]
	values = [1, 0] if has_user else [0, 1]
	
	return {
		"labels": labels,
		"datasets": [{"values": values}]
	}
