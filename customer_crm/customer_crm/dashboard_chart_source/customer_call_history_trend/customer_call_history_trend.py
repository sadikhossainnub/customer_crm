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
		SELECT DATE_FORMAT(call_date, '%%Y-%%m') as month, COUNT(name) as count
		FROM `tabCustomer Call`
		WHERE call_date IS NOT NULL {cond}
		GROUP BY month
		ORDER BY month DESC
		LIMIT 12
	""", val, as_dict=1)
	
	data.reverse()
	return {
		"labels": [d.month for d in data] if data else ["No Calls"],
		"datasets": [{"name": "Calls Count", "values": [d.count for d in data] if data else [0]}]
	}
