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
		SELECT DAY(posting_date) as day_of_month, COUNT(name) as count
		FROM `tabSales Invoice`
		WHERE docstatus = 1 {cond}
		GROUP BY day_of_month
		ORDER BY day_of_month ASC
	""", val, as_dict=1)
	
	labels = [str(i) for i in range(1, 32)]
	counts = [0] * 31
	for d in data:
		if 1 <= d.day_of_month <= 31:
			counts[d.day_of_month - 1] = d.count
			
	return {
		"labels": labels,
		"datasets": [{"name": "Average Orders", "values": counts}]
	}
