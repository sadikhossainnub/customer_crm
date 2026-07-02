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
		
	data = frappe.db.sql(f"""
		SELECT agent, COUNT(name) as count
		FROM `tabCustomer Call`
		WHERE agent IS NOT NULL AND agent != '' {cond}
		GROUP BY agent
		ORDER BY count DESC
		LIMIT 10
	""", val, as_dict=1)
	
	return {
		"labels": [d.agent for d in data] if data else ["No Agent"],
		"datasets": [{"name": "Call Records", "values": [d.count for d in data] if data else [0]}]
	}
