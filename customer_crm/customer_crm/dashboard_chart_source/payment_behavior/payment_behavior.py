import frappe
from frappe.utils import getdate, nowdate, flt


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
			si.name,
			si.grand_total,
			si.outstanding_amount,
			si.due_date,
			(
				SELECT MAX(pe.posting_date)
				FROM `tabPayment Entry Reference` per
				INNER JOIN `tabPayment Entry` pe ON pe.name = per.parent
				WHERE per.reference_doctype = 'Sales Invoice'
					AND per.reference_name = si.name
					AND pe.docstatus = 1
			) as last_payment_date
		FROM `tabSales Invoice` si
		WHERE si.docstatus = 1 AND si.is_return = 0 {where_clause}
	""", values, as_dict=1)

	on_time = 0
	late = 0
	unpaid = 0

	today = getdate(nowdate())

	for inv in data:
		due = getdate(inv.due_date) if inv.due_date else today
		outstanding = flt(inv.outstanding_amount)

		if outstanding >= flt(inv.grand_total):
			if due < today:
				late += 1
			else:
				unpaid += 1
		elif outstanding > 0:
			if inv.last_payment_date and getdate(inv.last_payment_date) <= due:
				on_time += 1
			else:
				late += 1
		else:
			if inv.last_payment_date and getdate(inv.last_payment_date) <= due:
				on_time += 1
			elif inv.last_payment_date:
				late += 1
			else:
				on_time += 1

	return {
		"labels": ["On-time", "Late", "Unpaid"],
		"datasets": [
			{
				"name": "Payment Status Ratio",
				"values": [on_time, late, unpaid]
			}
		]
	}
