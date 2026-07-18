import os
import json

base_dir = "/home/sayed/frappe-bench/apps/customer_crm/customer_crm/customer_crm"

charts_info = [
	{
		"name": "Order Frequency per Month",
		"folder": "order_frequency_per_month",
		"type": "Line",
		"py": """import frappe
from frappe.utils import getdate

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
		
	data = frappe.db.sql(f\"\"\"
		SELECT DATE_FORMAT(posting_date, '%%Y-%%m') as month, COUNT(name) as count
		FROM `tabSales Invoice`
		WHERE docstatus = 1 {cond}
		GROUP BY month
		ORDER BY month DESC
		LIMIT 12
	\"\"\", val, as_dict=1)
	
	data.reverse()
	return {
		"labels": [d.month for d in data],
		"datasets": [{"name": "Orders", "values": [d.count for d in data]}]
	}
"""
	},
	{
		"name": "Order Trend Graph",
		"folder": "order_trend_graph",
		"type": "Line",
		"py": """import frappe

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
		
	data = frappe.db.sql(f\"\"\"
		SELECT DAY(posting_date) as day_of_month, COUNT(name) as count
		FROM `tabSales Invoice`
		WHERE docstatus = 1 {cond}
		GROUP BY day_of_month
		ORDER BY day_of_month ASC
	\"\"\", val, as_dict=1)
	
	labels = [str(i) for i in range(1, 32)]
	counts = [0] * 31
	for d in data:
		if 1 <= d.day_of_month <= 31:
			counts[d.day_of_month - 1] = d.count
			
	return {
		"labels": labels,
		"datasets": [{"name": "Average Orders", "values": counts}]
	}
"""
	},
	{
		"name": "Total Address and Contact",
		"folder": "total_address_and_contact",
		"type": "Donut",
		"py": """import frappe

@frappe.whitelist()
def get(chart_name=None, chart=None, filters=None, **kwargs):
	if isinstance(filters, str):
		import json
		filters = json.loads(filters)
	filters = filters or {}
	customer = filters.get("customer") or filters.get("name")
	
	if not customer:
		return {"labels": [], "datasets": []}
		
	addr_count = frappe.db.count("Dynamic Link", {"link_doctype": "Customer", "link_name": customer, "parenttype": "Address"})
	contact_count = frappe.db.count("Dynamic Link", {"link_doctype": "Customer", "link_name": customer, "parenttype": "Contact"})
	
	return {
		"labels": ["Addresses", "Contacts"],
		"datasets": [{"values": [addr_count, contact_count]}]
	}
"""
	},
	{
		"name": "Order Channels",
		"folder": "order_channels",
		"type": "Bar",
		"py": """import frappe

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
		
	data = frappe.db.sql(f\"\"\"
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
	\"\"\", val, as_dict=1)
	
	return {
		"labels": [d.channel for d in data],
		"datasets": [{"name": "Sales Count", "values": [d.count for d in data]}]
	}
"""
	},
	{
		"name": "Total Spend Month Wise Comparison",
		"folder": "total_spend_comparison",
		"type": "Bar",
		"py": """import frappe
from frappe.utils import nowdate, getdate

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
		
	current_year = getdate(nowdate()).year
	years = [current_year - 2, current_year - 1, current_year]
	
	datasets = []
	months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
	
	for y in years:
		year_data = frappe.db.sql(f\"\"\"
			SELECT MONTH(posting_date) as month_num, SUM(grand_total) as total
			FROM `tabSales Invoice`
			WHERE docstatus = 1 AND YEAR(posting_date) = %(year)s {cond}
			GROUP BY month_num
		\"\"\", {**val, "year": y}, as_dict=1)
		
		vals = [0.0] * 12
		for d in year_data:
			if 1 <= d.month_num <= 12:
				vals[d.month_num - 1] = float(d.total or 0)
		datasets.append({"name": str(y), "values": vals})
		
	return {
		"labels": months,
		"datasets": datasets
	}
"""
	},
	{
		"name": "UTM Source Chart",
		"folder": "utm_source_chart",
		"type": "Bar",
		"py": """import frappe

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
		
	data = frappe.db.sql(f\"\"\"
		SELECT utm_source, COUNT(name) as count
		FROM `tabSales Invoice`
		WHERE docstatus = 1 AND utm_source IS NOT NULL AND utm_source != '' {cond}
		GROUP BY utm_source
		ORDER BY count DESC
	\"\"\", val, as_dict=1)
	
	return {
		"labels": [d.utm_source for d in data] if data else ["No UTM Source"],
		"datasets": [{"name": "Invoices", "values": [d.count for d in data] if data else [0]}]
	}
"""
	},
	{
		"name": "Customer Loyalty Points",
		"folder": "customer_loyalty_points",
		"type": "Donut",
		"py": """import frappe

@frappe.whitelist()
def get(chart_name=None, chart=None, filters=None, **kwargs):
	if isinstance(filters, str):
		import json
		filters = json.loads(filters)
	filters = filters or {}
	customer = filters.get("customer") or filters.get("name")
	
	if not customer:
		return {"labels": [], "datasets": []}
		
	earned = frappe.db.sql(\"\"\"
		SELECT SUM(loyalty_points) FROM `tabLoyalty Point Entry`
		WHERE customer = %(customer)s AND loyalty_points > 0
	\"\"\", {"customer": customer})[0][0] or 0
	
	spent = frappe.db.sql(\"\"\"
		SELECT SUM(loyalty_points) FROM `tabLoyalty Point Entry`
		WHERE customer = %(customer)s AND loyalty_points < 0
	\"\"\", {"customer": customer})[0][0] or 0
	
	return {
		"labels": ["Earned Points", "Redeemed Points"],
		"datasets": [{"values": [float(earned), float(abs(spent))]}]
	}
"""
	},
	{
		"name": "Website Account Status",
		"folder": "website_account_status",
		"type": "Pie",
		"py": """import frappe

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
		has_user = frappe.db.exists("Portal User", {"parent": customer, "parenttype": "Customer"})
		labels = ["Has Web Account", "No Web Account"]
		values = [1, 0] if has_user else [0, 1]
	else:
		total_customers = frappe.db.count("Customer", {"disabled": 0})
		portal_customers = frappe.db.sql(\"\"\"
			SELECT COUNT(DISTINCT parent)
			FROM `tabPortal User`
			WHERE parenttype = 'Customer'
		\"\"\")[0][0] or 0
		no_portal_customers = max(0, total_customers - portal_customers)
		
		labels = ["Has Web Account", "No Web Account"]
		values = [portal_customers, no_portal_customers]

	return {
		"labels": labels,
		"datasets": [{"values": values}]
	}
"""
	},
	{
		"name": "Purchased Items by Group",
		"folder": "purchased_items_by_group",
		"type": "Bar",
		"py": """import frappe

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
		cond = "AND si.customer = %(customer)s"
		val = {"customer": customer}
		
	data = frappe.db.sql(f\"\"\"
		SELECT i.item_group, SUM(sii.qty) as qty
		FROM `tabSales Invoice Item` sii
		INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
		INNER JOIN `tabItem` i ON i.item_code = sii.item_code
		WHERE si.docstatus = 1 {cond}
		GROUP BY i.item_group
		ORDER BY qty DESC
	\"\"\", val, as_dict=1)
	
	return {
		"labels": [d.item_group for d in data] if data else ["No Items"],
		"datasets": [{"name": "Quantity", "values": [float(d.qty) for d in data] if data else [0]}]
	}
"""
	},
	{
		"name": "Call Type Trend",
		"folder": "call_type_trend",
		"type": "Donut",
		"py": """import frappe

@frappe.whitelist()
def get(chart_name=None, chart=None, filters=None, **kwargs):
	if isinstance(filters, str):
		import json
		try:
			filters = json.loads(filters)
		except Exception:
			filters = {}
	filters = filters or {}
	customer = filters.get("customer") or filters.get("name")
	
	cond = ""
	val = {}
	if customer:
		cond = "AND customer = %(customer)s"
		val = {"customer": customer}
		
	data = frappe.db.sql(f\"\"\"
		SELECT call_type, COUNT(name) as count
		FROM `tabCustomer Call`
		WHERE call_type IS NOT NULL AND call_type != '' {cond}
		GROUP BY call_type
		ORDER BY count DESC
	\"\"\", val, as_dict=1)
	
	labels = [d.call_type for d in data]
	values = [d.count for d in data]
	
	if not labels:
		labels = ["No Calls"]
		values = [0]
		
	return {
		"labels": labels,
		"datasets": [{"values": values}]
	}
"""
	},
	{
		"name": "Complaints and Solution History",
		"folder": "complaints_and_solutions",
		"type": "Pie",
		"py": """import frappe

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
		
	open_issues = frappe.db.sql(f\"\"\"
		SELECT COUNT(name) FROM `tabIssue`
		WHERE status IN ('Open', 'Replied', 'On Hold') {cond}
	\"\"\", val)[0][0] or 0
	
	resolved = frappe.db.sql(f\"\"\"
		SELECT COUNT(name) FROM `tabIssue`
		WHERE status IN ('Resolved', 'Closed') {cond}
	\"\"\", val)[0][0] or 0
	
	return {
		"labels": ["Open Complaints", "Resolved/Closed"],
		"datasets": [{"values": [open_issues, resolved]}]
	}
"""
	},
	{
		"name": "Customer Call History Trend",
		"folder": "customer_call_history_trend",
		"type": "Line",
		"py": """import frappe

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
		
	data = frappe.db.sql(f\"\"\"
		SELECT DATE_FORMAT(call_date, '%%Y-%%m') as month, COUNT(name) as count
		FROM `tabCustomer Call`
		WHERE call_date IS NOT NULL {cond}
		GROUP BY month
		ORDER BY month DESC
		LIMIT 12
	\"\"\", val, as_dict=1)
	
	data.reverse()
	return {
		"labels": [d.month for d in data] if data else ["No Calls"],
		"datasets": [{"name": "Calls Count", "values": [d.count for d in data] if data else [0]}]
	}
"""
	},
	{
		"name": "Agent Call Record History",
		"folder": "agent_call_record_history",
		"type": "Bar",
		"py": """import frappe

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
		
	data = frappe.db.sql(f\"\"\"
		SELECT agent, COUNT(name) as count
		FROM `tabCustomer Call`
		WHERE agent IS NOT NULL AND agent != '' {cond}
		GROUP BY agent
		ORDER BY count DESC
		LIMIT 10
	\"\"\", val, as_dict=1)
	
	return {
		"labels": [d.agent for d in data] if data else ["No Agent"],
		"datasets": [{"name": "Call Records", "values": [d.count for d in data] if data else [0]}]
	}
"""
	},
	{
		"name": "Omni Channel Links Ratio",
		"folder": "omni_channel_links_ratio",
		"type": "Pie",
		"py": """import frappe

@frappe.whitelist()
def get(chart_name=None, chart=None, filters=None, **kwargs):
	if isinstance(filters, str):
		import json
		filters = json.loads(filters)
	filters = filters or {}
	customer = filters.get("customer") or filters.get("name")
	
	if not customer:
		return {"labels": [], "datasets": []}
		
	c_details = frappe.db.get_value("Customer", customer, ["website", "email_id", "mobile_no"], as_dict=1) or {}
	
	filled = 0
	empty = 0
	for field in ["website", "email_id", "mobile_no"]:
		if c_details.get(field):
			filled += 1
		else:
			empty += 1
			
	return {
		"labels": ["Channels Linked", "Channels Missing"],
		"datasets": [{"values": [filled, empty]}]
	}
"""
	},
	{
		"name": "Assigned Agent History Count",
		"folder": "assigned_agent_history_count",
		"type": "Bar",
		"py": """import frappe

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
		data = frappe.db.sql(\"\"\"
			SELECT owner, COUNT(name) as count
			FROM `tabCustomer`
			WHERE name = %(customer)s
			GROUP BY owner
		\"\"\", {"customer": customer}, as_dict=1)
	else:
		data = frappe.db.sql(\"\"\"
			SELECT owner, COUNT(name) as count
			FROM `tabCustomer`
			WHERE disabled = 0
				AND owner IS NOT NULL
				AND owner != ''
			GROUP BY owner
			ORDER BY count DESC
			LIMIT 15
		\"\"\", as_dict=1)

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
"""
	},
	{
		"name": "Sales Trend (Monthly)",
		"folder": "sales_trend_(monthly)",
		"type": "Line",
		"py": """import frappe

@frappe.whitelist()
def get(chart_name=None, chart=None, filters=None, **kwargs):
	if isinstance(filters, str):
		import json
		try:
			filters = json.loads(filters)
		except Exception:
			filters = {}
	filters = filters or {}
	customer = filters.get("customer") or filters.get("name")

	cond = ""
	val = {}
	if customer:
		cond = "AND customer = %(customer)s"
		val = {"customer": customer}

	data = frappe.db.sql(f\"\"\"
		SELECT DATE_FORMAT(posting_date, '%%Y-%%m') as month, SUM(grand_total) as total
		FROM `tabSales Invoice`
		WHERE docstatus = 1 {cond}
		GROUP BY month
		ORDER BY month DESC
		LIMIT 12
	\"\"\", val, as_dict=1)

	data.reverse()
	return {
		"labels": [d.month for d in data] if data else ["No Sales"],
		"datasets": [{"name": "Sales Amount", "values": [float(d.total or 0) for d in data] if data else [0.0]}]
	}
"""
	},
	{
		"name": "Credit Limit Utilization",
		"folder": "credit_limit_utilization",
		"type": "Donut",
		"py": """import frappe
from frappe.utils import flt

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
		data = frappe.db.sql(\"\"\"
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
		\"\"\", {"customer": customer}, as_dict=1)

		limit_val = 0.0
		outstanding = 0.0

		if data:
			limit_val = flt(data[0].credit_limit)
			outstanding = flt(data[0].current_outstanding)

		if limit_val == 0.0:
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
		data = frappe.db.sql(\"\"\"
			SELECT * FROM (
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
			) sub
			WHERE credit_limit > 0
			ORDER BY (current_outstanding / credit_limit) DESC
			LIMIT 10
		\"\"\", as_dict=1)

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
"""
	},
	{
		"name": "Outstanding Amount vs Paid",
		"folder": "outstanding_amount_vs_paid",
		"type": "Donut",
		"py": """import frappe
from frappe.utils import flt

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
	cond = ""
	val = {}
	if customer:
		cond = "AND customer = %(customer)s"
		val = {"customer": customer}

	data = frappe.db.sql(f\"\"\"
		SELECT
			COALESCE(SUM(grand_total), 0) as total_invoiced,
			COALESCE(SUM(outstanding_amount), 0) as total_outstanding,
			COALESCE(SUM(grand_total - outstanding_amount), 0) as total_paid
		FROM `tabSales Invoice`
		WHERE docstatus = 1 {cond}
	\"\"\", val, as_dict=1)

	total_paid = 0.0
	total_outstanding = 0.0

	if data:
		total_paid = flt(data[0].total_paid)
		total_outstanding = flt(data[0].total_outstanding)

	return {
		"labels": ["Paid Amount", "Outstanding Amount"],
		"datasets": [
			{
				"name": "Receivable Status",
				"values": [total_paid, total_outstanding]
			}
		]
	}
"""
	},
	{
		"name": "Payment Behavior",
		"folder": "payment_behavior",
		"type": "Pie",
		"py": """import frappe
from frappe.utils import getdate, nowdate, flt

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
		conditions.append("si.customer = %(customer)s")
		values["customer"] = customer

	where_clause = " AND ".join(conditions)
	if where_clause:
		where_clause = "AND " + where_clause

	data = frappe.db.sql(f\"\"\"
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
	\"\"\", values, as_dict=1)

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
"""
	},
	{
		"name": "Top Selling Items",
		"folder": "top_selling_items",
		"type": "Bar",
		"py": """import frappe
from frappe.utils import flt

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
		conditions.append("si.customer = %(customer)s")
		values["customer"] = customer

	where_clause = " AND ".join(conditions)
	if where_clause:
		where_clause = "AND " + where_clause

	data = frappe.db.sql(f\"\"\"
		SELECT
			sii.item_code,
			sii.item_name,
			SUM(sii.amount) as total_amount
		FROM `tabSales Invoice Item` sii
		INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
		WHERE si.docstatus = 1 {where_clause}
		GROUP BY sii.item_code
		ORDER BY total_amount DESC
		LIMIT 10
	\"\"\", values, as_dict=1)

	labels = [d.item_name or d.item_code for d in data]
	amounts = [flt(d.total_amount) for d in data]

	return {
		"labels": labels,
		"datasets": [
			{
				"name": "Sales Amount",
				"values": amounts
			}
		]
	}
"""
	},
	{
		"name": "Order Value Distribution",
		"folder": "order_value_distribution",
		"type": "Bar",
		"py": """import frappe
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

	min_max = frappe.db.sql(f\"\"\"
		SELECT
			MIN(grand_total) as min_val,
			MAX(grand_total) as max_val
		FROM `tabSales Invoice`
		WHERE docstatus = 1 {where_clause}
	\"\"\", values, as_dict=1)

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
	counts_data = frappe.db.sql(f\"\"\"
		SELECT {select_sql}
		FROM `tabSales Invoice`
		WHERE docstatus = 1 {where_clause}
	\"\"\", query_values, as_dict=1)

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
"""
	}
]

for chart in charts_info:
	source_dir = os.path.join(base_dir, "dashboard_chart_source", chart["folder"])
	os.makedirs(source_dir, exist_ok=True)
	
	# Write source init
	with open(os.path.join(source_dir, "__init__.py"), "w") as f:
		f.write(f"# {chart['name']} Init\n")
		
	# Write source JSON
	source_json = {
		"creation": "2026-07-02 15:40:00.000000",
		"docstatus": 0,
		"doctype": "Dashboard Chart Source",
		"idx": 0,
		"modified": "2026-07-02 15:40:00.000000",
		"modified_by": "Administrator",
		"module": "Customer CRM",
		"name": chart["name"],
		"owner": "Administrator",
		"source_name": chart["name"],
		"timeseries": 0
	}
	with open(os.path.join(source_dir, chart["folder"] + ".json"), "w") as f:
		json.dump(source_json, f, indent=1)
		
	# Write source Py
	with open(os.path.join(source_dir, chart["folder"] + ".py"), "w") as f:
		f.write(chart["py"])
		
	# Write source JS - writing real newlines and tabs directly
	source_js = f"""frappe.provide('frappe.dashboards.chart_sources');

frappe.dashboards.chart_sources['{chart["name"]}'] = {{
	method: 'customer_crm.customer_crm.dashboard_chart_source.{chart["folder"]}.{chart["folder"]}.get',
	filters: [
		{{
			fieldname: 'customer',
			label: __('Customer'),
			fieldtype: 'Link',
			options: 'Customer',
		}}
	],
}};
"""
	with open(os.path.join(source_dir, chart["folder"] + ".js"), "w") as f:
		f.write(source_js)
		
	# Write chart directory
	chart_dir = os.path.join(base_dir, "dashboard_chart", chart["folder"])
	os.makedirs(chart_dir, exist_ok=True)
	
	# Write chart JSON
	chart_json = {
		"based_on": "creation",
		"chart_name": chart["name"],
		"chart_type": "Custom",
		"creation": "2026-07-02 15:40:00.000000",
		"currency": "BDT",
		"docstatus": 0,
		"doctype": "Dashboard Chart",
		"document_type": "Customer",
		"dynamic_filters_json": "[]",
		"filters_json": "[]",
		"group_by_type": "Count",
		"idx": 0,
		"is_public": 1,
		"is_standard": 1,
		"modified": "2026-07-02 15:40:00.000000",
		"modified_by": "Administrator",
		"module": "Customer CRM",
		"name": chart["name"],
		"number_of_groups": 0,
		"owner": "Administrator",
		"parent_document_type": "",
		"roles": [],
		"show_values_over_chart": 1,
		"source": chart["name"],
		"time_interval": "Monthly",
		"timeseries": 0,
		"timespan": "Last Year",
		"type": chart["type"],
		"use_report_chart": 0,
		"value_based_on": "",
		"y_axis": []
	}
	with open(os.path.join(chart_dir, chart["folder"] + ".json"), "w") as f:
		json.dump(chart_json, f, indent=1)

print("Dashboard charts generated successfully!")
