import frappe
from frappe.utils import flt


@frappe.whitelist()
def get(
	chart_name=None,
	chart=None,
	no_cache=None,
	filters=None,
	from_date=None,
	to_date=None,
	timespan=None,
	time_interval=None,
	heatmap_year=None,
):
	# Calculate outstanding vs paid amount for Sales Invoices
	data = frappe.db.sql("""
		SELECT
			COALESCE(SUM(grand_total), 0) as total_invoiced,
			COALESCE(SUM(outstanding_amount), 0) as total_outstanding,
			COALESCE(SUM(grand_total - outstanding_amount), 0) as total_paid
		FROM `tabSales Invoice`
		WHERE docstatus = 1
	""", as_dict=1)

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
