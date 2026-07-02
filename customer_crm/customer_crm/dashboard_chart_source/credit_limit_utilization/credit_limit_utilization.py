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
	if isinstance(filters, str):
		import json
		try:
			filters = json.loads(filters)
		except Exception:
			filters = {}
	elif not filters:
		filters = {}

	customer = filters.get("customer") or filters.get("name")

	if customer:
		# Individual customer credit limit status
		data = frappe.db.sql("""
			SELECT
				c.name,
				COALESCE(
					(SELECT SUM(ccl.credit_limit)
					 FROM `tabCustomer Credit Limit` ccl
					 WHERE ccl.parent = c.name AND ccl.parenttype = 'Customer'),
					0
				) as credit_limit,
				COALESCE(
					(SELECT SUM(si.outstanding_amount)
					 FROM `tabSales Invoice` si
					 WHERE si.customer = c.name AND si.docstatus = 1 AND si.outstanding_amount > 0),
					0
				) as current_outstanding
			FROM `tabCustomer` c
			WHERE c.name = %(customer)s
		""", {"customer": customer}, as_dict=1)

		limit_val = 0.0
		outstanding = 0.0

		if data:
			limit_val = flt(data[0].credit_limit)
			outstanding = flt(data[0].current_outstanding)

		if limit_val == 0.0:
			# Default standard dummy return or alert
			return {
				"labels": ["No Credit Limit Set"],
				"datasets": [{"name": "Usage", "values": [0]}]
			}

		available = max(0.0, limit_val - outstanding)
		return {
			"labels": ["Utilized Credit", "Available Credit"],
			"datasets": [
				{
					"name": "Credit Status",
					"values": [outstanding, available]
				}
			]
		}
	else:
		# Top 10 customer utilization
		data = frappe.db.sql("""
			SELECT
				c.name as customer,
				c.customer_name,
				COALESCE(
					(SELECT SUM(ccl.credit_limit)
					 FROM `tabCustomer Credit Limit` ccl
					 WHERE ccl.parent = c.name AND ccl.parenttype = 'Customer'),
					0
				) as credit_limit,
				COALESCE(
					(SELECT SUM(si.outstanding_amount)
					 FROM `tabSales Invoice` si
					 WHERE si.customer = c.name AND si.docstatus = 1 AND si.outstanding_amount > 0),
					0
				) as current_outstanding
			FROM `tabCustomer` c
			WHERE c.disabled = 0
			HAVING credit_limit > 0
			ORDER BY (current_outstanding / credit_limit) DESC
			LIMIT 10
		""", as_dict=1)

		labels = [d.customer_name or d.customer for d in data]
		values = [round((flt(d.current_outstanding) / flt(d.credit_limit)) * 100, 1) if d.credit_limit else 0 for d in data]

		return {
			"labels": labels,
			"datasets": [
				{
					"name": "Utilization %",
					"values": values
				}
			]
		}
