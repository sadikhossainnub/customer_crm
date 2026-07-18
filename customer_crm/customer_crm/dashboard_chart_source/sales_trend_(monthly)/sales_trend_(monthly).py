import frappe

@frappe.whitelist()
def get(chart_name=None, chart=None, filters=None, **kwargs):
	if isinstance(filters, str):
		import json
		try:
			filters = json.loads(filters)
		except Exception:
			filters = {}
	filters = filters or {}
	customer = filters.get("customer") or filters.get("name")

	cond = ""
	val = {}
	if customer:
		cond = "AND customer = %(customer)s"
		val = {"customer": customer}

	data = frappe.db.sql(f"""
		SELECT DATE_FORMAT(posting_date, '%%Y-%%m') as month, SUM(grand_total) as total
		FROM `tabSales Invoice`
		WHERE docstatus = 1 {cond}
		GROUP BY month
		ORDER BY month DESC
		LIMIT 12
	""", val, as_dict=1)

	data.reverse()
	return {
		"labels": [d.month for d in data] if data else ["No Sales"],
		"datasets": [{"name": "Sales Amount", "values": [float(d.total or 0) for d in data] if data else [0.0]}]
	}
