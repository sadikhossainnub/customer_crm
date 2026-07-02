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
		cond = "AND customer = %(customer)s"
		val = {"customer": customer}
		
	open_issues = frappe.db.sql(f"""
		SELECT COUNT(name) FROM `tabIssue`
		WHERE status IN ('Open', 'Replied', 'On Hold') {cond}
	""", val)[0][0] or 0
	
	resolved = frappe.db.sql(f"""
		SELECT COUNT(name) FROM `tabIssue`
		WHERE status IN ('Resolved', 'Closed') {cond}
	""", val)[0][0] or 0
	
	return {
		"labels": ["Open Complaints", "Resolved/Closed"],
		"datasets": [{"values": [open_issues, resolved]}]
	}
