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
		cond = "AND si.customer = %(customer)s"
		val = {"customer": customer}
		
	data = frappe.db.sql(f"""
		SELECT i.item_group, SUM(sii.qty) as qty
		FROM `tabSales Invoice Item` sii
		INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
		INNER JOIN `tabItem` i ON i.item_code = sii.item_code
		WHERE si.docstatus = 1 {cond}
		GROUP BY i.item_group
		ORDER BY qty DESC
	""", val, as_dict=1)
	
	return {
		"labels": [d.item_group for d in data] if data else ["No Items"],
		"datasets": [{"name": "Quantity", "values": [float(d.qty) for d in data] if data else [0]}]
	}
