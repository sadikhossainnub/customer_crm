import frappe

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

	if customer:
		data = frappe.db.sql("""
			SELECT owner, COUNT(name) as count
			FROM `tabCustomer`
			WHERE name = %(customer)s
			GROUP BY owner
		""", {"customer": customer}, as_dict=1)
	else:
		data = frappe.db.sql("""
			SELECT owner, COUNT(name) as count
			FROM `tabCustomer`
			WHERE disabled = 0
				AND owner IS NOT NULL
				AND owner != ''
			GROUP BY owner
			ORDER BY count DESC
			LIMIT 15
		""", as_dict=1)

	labels = []
	for d in data:
		label = d.owner or "Unknown"
		if "@" in label:
			label = label.split("@")[0]
		labels.append(label)

	return {
		"labels": labels if labels else ["No Data"],
		"datasets": [{"name": "Customers Managed", "values": [d.count for d in data] if data else [0]}]
	}
