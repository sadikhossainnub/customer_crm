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
		cond = "AND parent = %(customer)s"
		val = {"customer": customer}
		
	data = frappe.db.sql(f"""
		SELECT owner, COUNT(name) as count
		FROM `tabCustomer`
		WHERE name IS NOT NULL {cond}
		GROUP BY owner
	""", val, as_dict=1)
	
	return {
		"labels": [d.owner for d in data],
		"datasets": [{"name": "Customers Owned", "values": [d.count for d in data]}]
	}
