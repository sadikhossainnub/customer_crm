import frappe
from frappe.utils import nowdate, getdate

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
		
	current_year = getdate(nowdate()).year
	years = [current_year - 2, current_year - 1, current_year]
	
	datasets = []
	months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
	
	for y in years:
		year_data = frappe.db.sql(f"""
			SELECT MONTH(posting_date) as month_num, SUM(grand_total) as total
			FROM `tabSales Invoice`
			WHERE docstatus = 1 AND YEAR(posting_date) = %(year)s {cond}
			GROUP BY month_num
		""", {**val, "year": y}, as_dict=1)
		
		vals = [0.0] * 12
		for d in year_data:
			if 1 <= d.month_num <= 12:
				vals[d.month_num - 1] = float(d.total or 0)
		datasets.append({"name": str(y), "values": vals})
		
	return {
		"labels": months,
		"datasets": datasets
	}
