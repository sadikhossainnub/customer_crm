import frappe
from frappe.utils import flt, cint

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
	conditions = []
	values = {}

	if customer:
		conditions.append("customer = %(customer)s")
		values["customer"] = customer

	where_clause = " AND ".join(conditions)
	if where_clause:
		where_clause = "AND " + where_clause

	min_max = frappe.db.sql(f"""
		SELECT
			MIN(grand_total) as min_val,
			MAX(grand_total) as max_val
		FROM `tabSales Invoice`
		WHERE docstatus = 1 {where_clause}
	""", values, as_dict=1)

	if not min_max or min_max[0].min_val is None:
		return {"labels": [], "datasets": []}

	min_val = flt(min_max[0].min_val)
	max_val = flt(min_max[0].max_val)

	if max_val <= min_val:
		return {
			"labels": [f"৳{int(min_val)}"],
			"datasets": [{"name": "Orders count", "values": [1]}]
		}

	num_buckets = 8
	bucket_width = (max_val - min_val) / num_buckets

	if bucket_width > 1000:
		bucket_width = round(bucket_width / 1000) * 1000
	elif bucket_width > 100:
		bucket_width = round(bucket_width / 100) * 100
	else:
		bucket_width = round(bucket_width / 10) * 10

	if bucket_width == 0:
		bucket_width = 1

	select_parts = []
	query_values = dict(values)

	for i in range(num_buckets):
		low = min_val + (i * bucket_width)
		high = low + bucket_width
		if i == num_buckets - 1:
			high = max(high, max_val + 1)
		query_values[f"low_{i}"] = low
		query_values[f"high_{i}"] = high
		select_parts.append(f"SUM(CASE WHEN grand_total >= %(low_{i})s AND grand_total < %(high_{i})s THEN 1 ELSE 0 END) as b_{i}")

	select_sql = ", ".join(select_parts)
	counts_data = frappe.db.sql(f"""
		SELECT {select_sql}
		FROM `tabSales Invoice`
		WHERE docstatus = 1 {where_clause}
	""", query_values, as_dict=1)

	labels = []
	values_list = []

	if counts_data:
		row = counts_data[0]
		for i in range(num_buckets):
			cnt = cint(row.get(f"b_{i}"))
			if cnt > 0:
				low = min_val + (i * bucket_width)
				high = low + bucket_width
				labels.append(f"৳{int(low)}-{int(high)}")
				values_list.append(cnt)

	return {
		"labels": labels,
		"datasets": [
			{
				"name": "Number of Orders",
				"values": values_list
			}
		]
	}
