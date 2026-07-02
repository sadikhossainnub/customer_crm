import frappe

@frappe.whitelist()
def get(chart_name=None, chart=None, filters=None, **kwargs):
	if isinstance(filters, str):
		import json
		filters = json.loads(filters)
	filters = filters or {}
	customer = filters.get("customer") or filters.get("name")
	
	cond = ""
	val = {}
	if customer:
		cond = "AND customer = %(customer)s"
		val = {"customer": customer}
		
	inbound = frappe.db.sql(f"""
		SELECT COUNT(name) FROM `tabCustomer Call`
		WHERE call_type = 'Inbound' {cond}
	""", val)[0][0] or 0
	
	outbound = frappe.db.sql(f"""
		SELECT COUNT(name) FROM `tabCustomer Call`
		WHERE call_type = 'Outbound' {cond}
	""", val)[0][0] or 0
	
	return {
		"labels": ["Inbound Calls", "Outbound Calls"],
		"datasets": [{"values": [inbound, outbound]}]
	}
