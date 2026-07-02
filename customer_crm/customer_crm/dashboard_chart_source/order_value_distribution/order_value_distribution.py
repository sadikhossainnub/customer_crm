import frappe
from frappe.utils import flt, cint


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

	if not min_max or not min_max[0].min_val:
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

	buckets = []
	for i in range(num_buckets):
		low = min_val + (i * bucket_width)
		high = low + bucket_width
		buckets.append({
			"low": low,
			"high": high,
			"bucket": f"৳{int(low)}-{int(high)}"
		})

	labels = []
	values_list = []

	for b in buckets:
		val_conditions = list(conditions)
		val_conditions.append("grand_total >= %(low)s")
		val_conditions.append("grand_total < %(high)s")
		val_where = " AND ".join(val_conditions)

		count = frappe.db.sql(f"""
			SELECT COUNT(name) as cnt
			FROM `tabSales Invoice`
			WHERE docstatus = 1 AND {val_where}
		""", {**values, "low": b["low"], "high": b["high"]}, as_dict=1)

		cnt = cint(count[0].cnt) if count else 0
		if cnt > 0:
			labels.append(b["bucket"])
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
