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
		
	c_details = frappe.db.get_value("Customer", customer, ["website", "email_id", "mobile_no"], as_dict=1) or {}
	
	filled = 0
	empty = 0
	for field in ["website", "email_id", "mobile_no"]:
		if c_details.get(field):
			filled += 1
		else:
			empty += 1
			
	return {
		"labels": ["Channels Linked", "Channels Missing"],
		"datasets": [{"values": [filled, empty]}]
	}
