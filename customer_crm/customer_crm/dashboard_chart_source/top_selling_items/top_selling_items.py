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
	# Parse filters
	if isinstance(filters, str):
		import json
		try:
			filters = json.loads(filters)
		except Exception:
			filters = {}
	elif not filters:
		filters = {}

	# If there's a dynamic customer filter (e.g. on Customer Dashboard)
	customer = filters.get("customer") or filters.get("name")

	# Query top selling items by amount
	conditions = []
	values = {}

	if customer:
		conditions.append("si.customer = %(customer)s")
		values["customer"] = customer

	where_clause = " AND ".join(conditions)
	if where_clause:
		where_clause = "AND " + where_clause

	data = frappe.db.sql(f"""
		SELECT
			sii.item_code,
			sii.item_name,
			SUM(sii.amount) as total_amount
		FROM `tabSales Invoice Item` sii
		INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
		WHERE si.docstatus = 1 {where_clause}
		GROUP BY sii.item_code
		ORDER BY total_amount DESC
		LIMIT 10
	""", values, as_dict=1)

	labels = [d.item_name or d.item_code for d in data]
	amounts = [flt(d.total_amount) for d in data]

	return {
		"labels": labels,
		"datasets": [
			{
				"name": "Sales Amount",
				"values": amounts
			}
		]
	}
