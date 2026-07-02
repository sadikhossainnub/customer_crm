import frappe
from frappe.utils import nowdate, add_months, getdate, flt, cint


@frappe.whitelist()
def get_dashboard_data(from_date=None, to_date=None):
	"""Main API: returns all dashboard data in a single call"""
	if not from_date:
		from_date = add_months(nowdate(), -12)
	if not to_date:
		to_date = nowdate()

	return {
		"new_customers_trend": get_new_customers_trend(from_date, to_date),
		"customer_wise_revenue": get_customer_wise_revenue(from_date, to_date),
		"customer_group_sales": get_customer_group_sales(from_date, to_date),
		"territory_sales": get_territory_sales(from_date, to_date),
		"customer_lifetime_value": get_customer_lifetime_value(),
		"loyalty_points": get_loyalty_points_balance(),
		"repeat_vs_new": get_repeat_vs_new_ratio(from_date, to_date),
		"avg_order_value_trend": get_avg_order_value_trend(from_date, to_date),
		"inactive_customers": get_inactive_customers(),
		"summary_cards": get_summary_cards(from_date, to_date),
		"sales_trend_monthly": get_sales_trend_monthly(from_date, to_date),
		"outstanding_vs_paid": get_outstanding_vs_paid(from_date, to_date),
		"top_selling_items": get_top_selling_items(from_date, to_date),
		"order_value_distribution": get_order_value_distribution(from_date, to_date),
		"payment_behavior": get_payment_behavior(from_date, to_date),
		"credit_limit_utilization": get_credit_limit_utilization(),
	}


def get_new_customers_trend(from_date, to_date):
	"""Monthly customer acquisition trend"""
	data = frappe.db.sql("""
		SELECT
			DATE_FORMAT(creation, '%%Y-%%m') as month,
			COUNT(name) as count
		FROM `tabCustomer`
		WHERE creation BETWEEN %(from_date)s AND %(to_date)s
			AND disabled = 0
		GROUP BY DATE_FORMAT(creation, '%%Y-%%m')
		ORDER BY month
	""", {"from_date": from_date, "to_date": to_date}, as_dict=1)
	return data


def get_customer_wise_revenue(from_date, to_date):
	"""Top 10 customers by revenue"""
	data = frappe.db.sql("""
		SELECT
			si.customer as customer,
			si.customer_name as customer_name,
			SUM(si.grand_total) as total_revenue
		FROM `tabSales Invoice` si
		WHERE si.docstatus = 1
			AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
		GROUP BY si.customer
		ORDER BY total_revenue DESC
		LIMIT 10
	""", {"from_date": from_date, "to_date": to_date}, as_dict=1)
	return data


def get_customer_group_sales(from_date, to_date):
	"""Sales distribution by customer group"""
	data = frappe.db.sql("""
		SELECT
			c.customer_group as customer_group,
			SUM(si.grand_total) as total_sales
		FROM `tabSales Invoice` si
		INNER JOIN `tabCustomer` c ON si.customer = c.name
		WHERE si.docstatus = 1
			AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
			AND c.customer_group IS NOT NULL
			AND c.customer_group != ''
		GROUP BY c.customer_group
		ORDER BY total_sales DESC
	""", {"from_date": from_date, "to_date": to_date}, as_dict=1)
	return data


def get_territory_sales(from_date, to_date):
	"""Sales distribution by territory"""
	data = frappe.db.sql("""
		SELECT
			si.territory as territory,
			SUM(si.grand_total) as total_sales,
			COUNT(DISTINCT si.customer) as customer_count
		FROM `tabSales Invoice` si
		WHERE si.docstatus = 1
			AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
			AND si.territory IS NOT NULL
			AND si.territory != ''
		GROUP BY si.territory
		ORDER BY total_sales DESC
	""", {"from_date": from_date, "to_date": to_date}, as_dict=1)
	return data


def get_customer_lifetime_value():
	"""Customer Lifetime Value - total revenue from each customer over all time"""
	data = frappe.db.sql("""
		SELECT
			si.customer as customer,
			si.customer_name as customer_name,
			c.customer_group as customer_group,
			c.territory as territory,
			SUM(si.grand_total) as lifetime_value,
			COUNT(si.name) as total_orders,
			MIN(si.posting_date) as first_order,
			MAX(si.posting_date) as last_order,
			DATEDIFF(MAX(si.posting_date), MIN(si.posting_date)) as customer_age_days,
			ROUND(SUM(si.grand_total) / COUNT(si.name), 2) as avg_order_value
		FROM `tabSales Invoice` si
		INNER JOIN `tabCustomer` c ON si.customer = c.name
		WHERE si.docstatus = 1
		GROUP BY si.customer
		ORDER BY lifetime_value DESC
		LIMIT 20
	""", as_dict=1)
	return data


def get_loyalty_points_balance():
	"""Get loyalty points balance for customers"""
	# Check if Loyalty Point Entry exists
	if not frappe.db.table_exists("tabLoyalty Point Entry"):
		return []

	data = frappe.db.sql("""
		SELECT
			lpe.customer as customer,
			lpe.customer_name as customer_name,
			SUM(lpe.loyalty_points) as points_balance,
			MAX(lpe.posting_date) as last_activity
		FROM `tabLoyalty Point Entry` lpe
		WHERE lpe.docstatus < 2
		GROUP BY lpe.customer
		HAVING points_balance > 0
		ORDER BY points_balance DESC
		LIMIT 15
	""", as_dict=1)
	return data


def get_repeat_vs_new_ratio(from_date, to_date):
	"""Ratio of repeat vs new customers in the given period"""
	# Customers who placed orders in this period
	customers_in_period = frappe.db.sql("""
		SELECT DISTINCT customer
		FROM `tabSales Invoice`
		WHERE docstatus = 1
			AND posting_date BETWEEN %(from_date)s AND %(to_date)s
	""", {"from_date": from_date, "to_date": to_date}, as_list=1)

	total = len(customers_in_period)
	if not total:
		return {"new": 0, "repeat": 0, "total": 0}

	# Check which ones had orders BEFORE the period
	customer_list = [c[0] for c in customers_in_period]
	if not customer_list:
		return {"new": 0, "repeat": 0, "total": 0}

	repeat_customers = frappe.db.sql("""
		SELECT COUNT(DISTINCT customer) as cnt
		FROM `tabSales Invoice`
		WHERE docstatus = 1
			AND posting_date < %(from_date)s
			AND customer IN %(customers)s
	""", {"from_date": from_date, "customers": customer_list}, as_dict=1)

	repeat_count = cint(repeat_customers[0].cnt) if repeat_customers else 0
	new_count = total - repeat_count

	return {
		"new": new_count,
		"repeat": repeat_count,
		"total": total
	}


def get_avg_order_value_trend(from_date, to_date):
	"""Average order value trend by month"""
	data = frappe.db.sql("""
		SELECT
			DATE_FORMAT(posting_date, '%%Y-%%m') as month,
			ROUND(AVG(grand_total), 2) as avg_value,
			COUNT(name) as order_count,
			SUM(grand_total) as total_revenue
		FROM `tabSales Invoice`
		WHERE docstatus = 1
			AND posting_date BETWEEN %(from_date)s AND %(to_date)s
		GROUP BY DATE_FORMAT(posting_date, '%%Y-%%m')
		ORDER BY month
	""", {"from_date": from_date, "to_date": to_date}, as_dict=1)
	return data


def get_inactive_customers(days_threshold=90):
	"""Customers whose last transaction is older than the threshold"""
	threshold_date = add_months(nowdate(), -3)

	data = frappe.db.sql("""
		SELECT
			c.name as customer,
			c.customer_name as customer_name,
			c.customer_group as customer_group,
			c.territory as territory,
			MAX(si.posting_date) as last_transaction_date,
			DATEDIFF(CURDATE(), MAX(si.posting_date)) as days_since_last_order,
			COUNT(si.name) as total_orders,
			SUM(si.grand_total) as total_spent
		FROM `tabCustomer` c
		INNER JOIN `tabSales Invoice` si ON si.customer = c.name AND si.docstatus = 1
		WHERE c.disabled = 0
		GROUP BY c.name
		HAVING last_transaction_date < %(threshold_date)s
		ORDER BY days_since_last_order DESC
		LIMIT 20
	""", {"threshold_date": threshold_date}, as_dict=1)
	return data


def get_summary_cards(from_date, to_date):
	"""Summary numbers for the dashboard header cards"""
	total_customers = frappe.db.count("Customer", {"disabled": 0})

	# New customers in period
	new_customers = frappe.db.sql("""
		SELECT COUNT(name) as cnt FROM `tabCustomer`
		WHERE creation BETWEEN %(from_date)s AND %(to_date)s AND disabled = 0
	""", {"from_date": from_date, "to_date": to_date}, as_dict=1)

	# Total revenue in period
	revenue = frappe.db.sql("""
		SELECT
			COALESCE(SUM(grand_total), 0) as total,
			COUNT(name) as order_count
		FROM `tabSales Invoice`
		WHERE docstatus = 1
			AND posting_date BETWEEN %(from_date)s AND %(to_date)s
	""", {"from_date": from_date, "to_date": to_date}, as_dict=1)

	# Average order value
	avg_order = flt(revenue[0].total) / max(cint(revenue[0].order_count), 1) if revenue else 0

	# Active customers (ordered in last 90 days)
	active_customers = frappe.db.sql("""
		SELECT COUNT(DISTINCT customer) as cnt
		FROM `tabSales Invoice`
		WHERE docstatus = 1
			AND posting_date >= DATE_SUB(CURDATE(), INTERVAL 90 DAY)
	""", as_dict=1)

	return {
		"total_customers": cint(total_customers),
		"new_customers": cint(new_customers[0].cnt) if new_customers else 0,
		"total_revenue": flt(revenue[0].total) if revenue else 0,
		"total_orders": cint(revenue[0].order_count) if revenue else 0,
		"avg_order_value": flt(avg_order, 2),
		"active_customers": cint(active_customers[0].cnt) if active_customers else 0,
	}


def get_sales_trend_monthly(from_date, to_date):
	"""Monthly sales trend based on Sales Invoice"""
	data = frappe.db.sql("""
		SELECT
			DATE_FORMAT(posting_date, '%%Y-%%m') as month,
			SUM(grand_total) as total_sales,
			COUNT(name) as invoice_count
		FROM `tabSales Invoice`
		WHERE docstatus = 1
			AND posting_date BETWEEN %(from_date)s AND %(to_date)s
		GROUP BY DATE_FORMAT(posting_date, '%%Y-%%m')
		ORDER BY month
	""", {"from_date": from_date, "to_date": to_date}, as_dict=1)
	return data


def get_outstanding_vs_paid(from_date, to_date):
	"""Outstanding amount vs paid amount from Sales Invoices"""
	data = frappe.db.sql("""
		SELECT
			COALESCE(SUM(grand_total), 0) as total_invoiced,
			COALESCE(SUM(outstanding_amount), 0) as total_outstanding,
			COALESCE(SUM(grand_total - outstanding_amount), 0) as total_paid
		FROM `tabSales Invoice`
		WHERE docstatus = 1
			AND posting_date BETWEEN %(from_date)s AND %(to_date)s
	""", {"from_date": from_date, "to_date": to_date}, as_dict=1)

	if data:
		return {
			"total_invoiced": flt(data[0].total_invoiced),
			"total_outstanding": flt(data[0].total_outstanding),
			"total_paid": flt(data[0].total_paid),
		}
	return {"total_invoiced": 0, "total_outstanding": 0, "total_paid": 0}


def get_top_selling_items(from_date, to_date):
	"""Top 15 items by sales quantity/amount across all customers"""
	data = frappe.db.sql("""
		SELECT
			sii.item_code,
			sii.item_name,
			SUM(sii.qty) as total_qty,
			SUM(sii.amount) as total_amount
		FROM `tabSales Invoice Item` sii
		INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
		WHERE si.docstatus = 1
			AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
		GROUP BY sii.item_code
		ORDER BY total_amount DESC
		LIMIT 15
	""", {"from_date": from_date, "to_date": to_date}, as_dict=1)
	return data


def get_order_value_distribution(from_date, to_date):
	"""Distribution of order values into histogram buckets"""
	# First get min/max to define buckets
	min_max = frappe.db.sql("""
		SELECT
			MIN(grand_total) as min_val,
			MAX(grand_total) as max_val
		FROM `tabSales Invoice`
		WHERE docstatus = 1
			AND posting_date BETWEEN %(from_date)s AND %(to_date)s
	""", {"from_date": from_date, "to_date": to_date}, as_dict=1)

	if not min_max or not min_max[0].min_val:
		return []

	min_val = flt(min_max[0].min_val)
	max_val = flt(min_max[0].max_val)

	if max_val <= min_val:
		return [{"bucket": f"৳{int(min_val)}", "count": 1}]

	# Create 8 equal-width buckets
	num_buckets = 8
	bucket_width = (max_val - min_val) / num_buckets

	# Round bucket_width to a nice number
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

	# Count orders in each bucket
	result = []
	for b in buckets:
		count = frappe.db.sql("""
			SELECT COUNT(name) as cnt
			FROM `tabSales Invoice`
			WHERE docstatus = 1
				AND posting_date BETWEEN %(from_date)s AND %(to_date)s
				AND grand_total >= %(low)s
				AND grand_total < %(high)s
		""", {
				"from_date": from_date, "to_date": to_date,
				"low": b["low"], "high": b["high"]
			}, as_dict=1)
		cnt = cint(count[0].cnt) if count else 0
		if cnt > 0:
			result.append({"bucket": b["bucket"], "count": cnt})

	return result


def get_payment_behavior(from_date, to_date):
	"""On-time vs late payment ratio based on due_date vs payment clearing"""
	# Compare Sales Invoice due_date with the actual payment date
	# An invoice is "on-time" if fully paid by its due_date
	# An invoice is "late" if outstanding > 0 after due_date, or paid after due_date
	# An invoice is "unpaid" if still outstanding

	data = frappe.db.sql("""
		SELECT
			si.name,
			si.grand_total,
			si.outstanding_amount,
			si.due_date,
			si.status,
			(
				SELECT MAX(pe.posting_date)
				FROM `tabPayment Entry Reference` per
				INNER JOIN `tabPayment Entry` pe ON pe.name = per.parent
				WHERE per.reference_doctype = 'Sales Invoice'
					AND per.reference_name = si.name
					AND pe.docstatus = 1
			) as last_payment_date
		FROM `tabSales Invoice` si
		WHERE si.docstatus = 1
			AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
			AND si.is_return = 0
	""", {"from_date": from_date, "to_date": to_date}, as_dict=1)

	on_time = 0
	late = 0
	unpaid = 0

	today = getdate(nowdate())

	for inv in data:
		due = getdate(inv.due_date) if inv.due_date else today
		outstanding = flt(inv.outstanding_amount)

		if outstanding >= flt(inv.grand_total):
			# Fully unpaid
			if due < today:
				late += 1
			else:
				unpaid += 1
		elif outstanding > 0:
			# Partially paid
			if inv.last_payment_date and getdate(inv.last_payment_date) <= due:
				on_time += 1
			else:
				late += 1
		else:
			# Fully paid
			if inv.last_payment_date and getdate(inv.last_payment_date) <= due:
				on_time += 1
			elif inv.last_payment_date:
				late += 1
			else:
				# Paid but no payment entry (e.g., journal entry or write-off)
				on_time += 1

	return {
		"on_time": on_time,
		"late": late,
		"unpaid": unpaid,
		"total": len(data)
	}


def get_credit_limit_utilization():
	"""Credit limit utilization for customers who have a credit limit set"""
	# Get customers with credit limits from Customer Credit Limit child table or customer field
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

	result = []
	for d in data:
		limit_val = flt(d.credit_limit)
		outstanding = flt(d.current_outstanding)
		pct = round((outstanding / limit_val) * 100, 1) if limit_val else 0
		result.append({
			"customer": d.customer,
			"customer_name": d.customer_name,
			"credit_limit": limit_val,
			"current_outstanding": outstanding,
			"utilization_pct": min(pct, 100),
			"over_limit": outstanding > limit_val,
		})

	return result
