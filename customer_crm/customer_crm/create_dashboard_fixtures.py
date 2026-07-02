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
		filters = json.loads(filters)
	filters = filters or {}
	customer = filters.get("customer") or filters.get("name")
	
	if not customer:
		return {"labels": [], "datasets": []}
		
	has_user = frappe.db.exists("Portal User", {"parent": customer})
	labels = ["Has Web Account", "No Web Account"]
	values = [1, 0] if has_user else [0, 1]
	
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
		filters = json.loads(filters)
	filters = filters or {}
	customer = filters.get("customer") or filters.get("name")
	
	cond = ""
	val = {}
	if customer:
		cond = "AND customer = %(customer)s"
		val = {"customer": customer}
		
	inbound = frappe.db.sql(f\"\"\"
		SELECT COUNT(name) FROM `tabCustomer Call`
		WHERE call_type = 'Inbound' {cond}
	\"\"\", val)[0][0] or 0
	
	outbound = frappe.db.sql(f\"\"\"
		SELECT COUNT(name) FROM `tabCustomer Call`
		WHERE call_type = 'Outbound' {cond}
	\"\"\", val)[0][0] or 0
	
	return {
		"labels": ["Inbound Calls", "Outbound Calls"],
		"datasets": [{"values": [inbound, outbound]}]
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
		filters = json.loads(filters)
	filters = filters or {}
	customer = filters.get("customer") or filters.get("name")
	
	cond = ""
	val = {}
	if customer:
		cond = "AND parent = %(customer)s"
		val = {"customer": customer}
		
	data = frappe.db.sql(f\"\"\"
		SELECT owner, COUNT(name) as count
		FROM `tabCustomer`
		WHERE name IS NOT NULL {cond}
		GROUP BY owner
	\"\"\", val, as_dict=1)
	
	return {
		"labels": [d.owner for d in data],
		"datasets": [{"name": "Customers Owned", "values": [d.count for d in data]}]
	}
"""
	}
]

for chart in charts_info:
	source_dir = os.path.join(base_dir, "dashboard_chart_source", chart["folder"])
	os.makedirs(source_dir, exist_ok=True)
	
	# Write source init
	with open(os.path.join(source_dir, "__init__.py"), "w") as f:
		f.write(f"# {chart['name']} Init\\n")
		
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
		
	# Write source JS
	source_js = "frappe.provide('frappe.dashboards.chart_sources');\\n\\nfrappe.dashboards.chart_sources['" + chart["name"] + "'] = {\\n\\tmethod: 'customer_crm.customer_crm.dashboard_chart_source." + chart["folder"] + "." + chart["folder"] + ".get',\\n\\tfilters: [\\n\\t\\t{\\n\\t\\t\\tfieldname: 'customer',\\n\\t\\t\\tlabel: __('Customer'),\\n\\t\\t\\tfieldtype: 'Link',\\n\\t\\t\\toptions: 'Customer',\\n\\t\\t}\\n\\t],\\n};\\n"
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
