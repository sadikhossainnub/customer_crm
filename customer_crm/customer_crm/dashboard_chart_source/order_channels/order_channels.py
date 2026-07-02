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
		
	data = frappe.db.sql(f"""
		SELECT 
			CASE 
				WHEN is_pos = 1 THEN 'POS'
				WHEN utm_source IS NOT NULL AND utm_source != '' THEN utm_source
				WHEN source IS NOT NULL AND source != '' THEN source
				ELSE 'Direct/Other'
			END as channel,
			COUNT(name) as count
		FROM `tabSales Invoice`
		WHERE docstatus = 1 {cond}
		GROUP BY channel
		ORDER BY count DESC
	""", val, as_dict=1)
	
	return {
		"labels": [d.channel for d in data],
		"datasets": [{"name": "Sales Count", "values": [d.count for d in data]}]
	}
