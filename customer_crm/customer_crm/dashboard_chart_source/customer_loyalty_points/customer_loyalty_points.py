import frappe

@frappe.whitelist()
def get(chart_name=None, chart=None, filters=None, **kwargs):
	if isinstance(filters, str):
		import json
		filters = json.loads(filters)
	filters = filters or {}
	customer = filters.get("customer") or filters.get("name")
	
	if not customer:
		return {"labels": [], "datasets": []}
		
	earned = frappe.db.sql("""
		SELECT SUM(loyalty_points) FROM `tabLoyalty Point Entry`
		WHERE customer = %(customer)s AND loyalty_points > 0
	""", {"customer": customer})[0][0] or 0
	
	spent = frappe.db.sql("""
		SELECT SUM(loyalty_points) FROM `tabLoyalty Point Entry`
		WHERE customer = %(customer)s AND loyalty_points < 0
	""", {"customer": customer})[0][0] or 0
	
	return {
		"labels": ["Earned Points", "Redeemed Points"],
		"datasets": [{"values": [float(earned), float(abs(spent))]}]
	}
