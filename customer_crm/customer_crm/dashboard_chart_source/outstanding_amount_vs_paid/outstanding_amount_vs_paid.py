import frappe
from frappe.utils import flt

@frappe.whitelist()
def get(chart_name=None, chart=None, filters=None, **kwargs):
	if isinstance(filters, str):
		import json
		try:
			filters = json.loads(filters)
		except Exception:
			filters = {}
	elif not filters:
		filters = {}

	customer = filters.get("customer") or filters.get("name")
	cond = ""
	val = {}
	if customer:
		cond = "AND customer = %(customer)s"
		val = {"customer": customer}

	data = frappe.db.sql(f"""
		SELECT
			COALESCE(SUM(grand_total), 0) as total_invoiced,
			COALESCE(SUM(outstanding_amount), 0) as total_outstanding,
			COALESCE(SUM(grand_total - outstanding_amount), 0) as total_paid
		FROM `tabSales Invoice`
		WHERE docstatus = 1 {cond}
	""", val, as_dict=1)

	total_paid = 0.0
	total_outstanding = 0.0

	if data:
		total_paid = flt(data[0].total_paid)
		total_outstanding = flt(data[0].total_outstanding)

	return {
		"labels": ["Paid Amount", "Outstanding Amount"],
		"datasets": [
			{
				"name": "Receivable Status",
				"values": [total_paid, total_outstanding]
			}
		]
	}
