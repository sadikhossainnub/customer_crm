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
		SELECT utm_source, COUNT(name) as count
		FROM `tabSales Invoice`
		WHERE docstatus = 1 AND utm_source IS NOT NULL AND utm_source != '' {cond}
		GROUP BY utm_source
		ORDER BY count DESC
	""", val, as_dict=1)
	
	return {
		"labels": [d.utm_source for d in data] if data else ["No UTM Source"],
		"datasets": [{"name": "Invoices", "values": [d.count for d in data] if data else [0]}]
	}
