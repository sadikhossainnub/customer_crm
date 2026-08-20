import frappe
from frappe import _
from frappe.utils import today, flt, round_based_on_smallest_currency_fraction


def execute(filters=None):
	filters = filters or {}
	columns = get_columns(filters)
	data = get_data(filters)
	chart = get_chart(data, filters)
	summary = get_summary(data, filters)
	return columns, data, None, chart, summary


def get_columns(filters):
	doc_type = filters.get("doc_type") or "Sales Invoice"
	doc_type_label = _(doc_type)

	cols = [
		{
			"label": _("Agent"),
			"fieldname": "agent",
			"fieldtype": "Link",
			"options": "User",
			"width": 180
		},
		{
			"label": _("Agent Name"),
			"fieldname": "agent_name",
			"fieldtype": "Data",
			"width": 160
		},
		{
			"label": _("Assigned Customers"),
			"fieldname": "assigned_customers",
			"fieldtype": "Int",
			"width": 140
		},
		{
			"label": _("Total Calls"),
			"fieldname": "total_calls",
			"fieldtype": "Int",
			"width": 110
		},
		{
			"label": _("Interested Calls"),
			"fieldname": "interested_calls",
			"fieldtype": "Int",
			"width": 130
		},
		{
			"label": f"{doc_type_label} " + _("Count"),
			"fieldname": "doc_count",
			"fieldtype": "Int",
			"width": 130
		},
		{
			"label": _("Total Sales"),
			"fieldname": "total_sales",
			"fieldtype": "Currency",
			"options": "Currency",
			"width": 140
		}
	]

	if doc_type == "Sales Invoice":
		cols.extend([
			{
				"label": _("Paid Amount"),
				"fieldname": "paid_amount",
				"fieldtype": "Currency",
				"options": "Currency",
				"width": 130
			},
			{
				"label": _("Outstanding Amount"),
				"fieldname": "outstanding_amount",
				"fieldtype": "Currency",
				"options": "Currency",
				"width": 140
			}
		])

	cols.extend([
		{
			"label": _("Avg Order Value"),
			"fieldname": "avg_value",
			"fieldtype": "Currency",
			"options": "Currency",
			"width": 130
		},
		{
			"label": _("Conversion Rate %"),
			"fieldname": "conversion_rate",
			"fieldtype": "Percent",
			"width": 130
		}
	])

	return cols


def get_data(filters):
	doc_type = filters.get("doc_type") or "Sales Invoice"
	from_date = filters.get("from_date") or today()
	to_date = filters.get("to_date") or today()
	agent_filter = filters.get("agent")
	customer_group = filters.get("customer_group")
	status_filter = filters.get("status")
	date_based_on = filters.get("date_based_on") or "Posting/Transaction Date"

	# 1. Fetch Call Stats per Agent
	call_conditions = "call_date BETWEEN %(from_date)s AND %(to_date)s"
	call_args = {"from_date": from_date, "to_date": to_date}
	if agent_filter:
		call_conditions += " AND agent = %(agent)s"
		call_args["agent"] = agent_filter

	calls_query = frappe.db.sql(f"""
		SELECT
			agent,
			COUNT(*) AS total_calls,
			SUM(CASE WHEN call_outcome = 'Interested' THEN 1 ELSE 0 END) AS interested_calls
		FROM `tabCustomer Call`
		WHERE {call_conditions}
		GROUP BY agent
	""", call_args, as_dict=True)

	call_map = {r.agent: r for r in calls_query if r.agent}

	# 2. Fetch Assigned Customer Counts per Agent
	assign_conditions = "ca.is_active = 1 AND ca.from_date <= %(to_date)s AND ca.to_date >= %(from_date)s"
	assign_args = {"from_date": from_date, "to_date": to_date}
	if agent_filter:
		assign_conditions += " AND caa.agent = %(agent)s"
		assign_args["agent"] = agent_filter

	assignments_query = frappe.db.sql(f"""
		SELECT
			caa.agent,
			COUNT(DISTINCT cac.customer) AS assigned_customers
		FROM `tabCustomer Assignment Agent` caa
		JOIN `tabCustomer Assignment` ca ON ca.name = caa.parent
		JOIN `tabCustomer Assignment Customer` cac ON cac.parent = ca.name
		WHERE {assign_conditions}
		GROUP BY caa.agent
	""", assign_args, as_dict=True)

	assignment_map = {r.agent: r.assigned_customers for r in assignments_query if r.agent}

	# 3. Determine Date Field Name
	if date_based_on == "Due Date":
		if doc_type == "Sales Invoice":
			date_field_expr = "dt.due_date"
		elif doc_type == "Sales Order":
			date_field_expr = "COALESCE(dt.delivery_date, dt.transaction_date)"
		else:
			date_field_expr = "dt.posting_date"
	elif date_based_on == "Creation Date":
		date_field_expr = "DATE(dt.creation)"
	else: # Default: Posting/Transaction Date
		if doc_type == "Sales Order":
			date_field_expr = "dt.transaction_date"
		else:
			date_field_expr = "dt.posting_date"

	# Build Document Conditions & Fetch Sales Documents
	doc_conditions = [f"{date_field_expr} BETWEEN %(from_date)s AND %(to_date)s"]
	doc_args = {"from_date": from_date, "to_date": to_date}

	if status_filter:
		if status_filter == "Submitted":
			doc_conditions.append("dt.docstatus = 1")
		elif status_filter == "Draft":
			doc_conditions.append("dt.docstatus = 0")
		elif status_filter == "Cancelled":
			doc_conditions.append("dt.docstatus = 2")
		else:
			doc_conditions.append("dt.docstatus = 1")
			doc_conditions.append("dt.status = %(status)s")
			doc_args["status"] = status_filter
	else:
		doc_conditions.append("dt.docstatus = 1")

	if customer_group:
		doc_conditions.append("cust.customer_group = %(customer_group)s")
		doc_args["customer_group"] = customer_group

	where_clause = " AND ".join(doc_conditions)

	select_paid_outstanding = ""
	if doc_type == "Sales Invoice":
		select_paid_outstanding = ", COALESCE(dt.paid_amount, 0) as paid_amount, COALESCE(dt.outstanding_amount, 0) as outstanding_amount"

	documents = frappe.db.sql(f"""
		SELECT
			dt.name,
			dt.customer,
			{date_field_expr} as doc_date,
			dt.grand_total,
			dt.owner
			{select_paid_outstanding}
		FROM `tab{doc_type}` dt
		LEFT JOIN `tabCustomer` cust ON cust.name = dt.customer
		WHERE {where_clause}
	""", doc_args, as_dict=True)

	# 4. Map Documents to Agents (Customer Assignment -> Owner Fallback)
	cust_assignments = frappe.db.sql("""
		SELECT
			cac.customer,
			caa.agent,
			ca.from_date,
			ca.to_date
		FROM `tabCustomer Assignment` ca
		JOIN `tabCustomer Assignment Customer` cac ON cac.parent = ca.name
		JOIN `tabCustomer Assignment Agent` caa ON caa.parent = ca.name
		WHERE ca.is_active = 1
	""", as_dict=True)

	def resolve_agent(customer, check_date, owner):
		if customer and check_date:
			for ca in cust_assignments:
				if ca.customer == customer and ca.from_date <= check_date and ca.to_date >= check_date:
					return ca.agent
		return owner

	agent_sales_map = {}

	for d in documents:
		agent = resolve_agent(d.customer, d.doc_date, d.owner)

		if agent_filter and agent != agent_filter:
			continue

		if agent not in agent_sales_map:
			agent_sales_map[agent] = {
				"doc_count": 0,
				"total_sales": 0.0,
				"paid_amount": 0.0,
				"outstanding_amount": 0.0
			}

		entry = agent_sales_map[agent]
		entry["doc_count"] += 1
		entry["total_sales"] += flt(d.grand_total)
		if doc_type == "Sales Invoice":
			entry["paid_amount"] += flt(d.paid_amount)
			entry["outstanding_amount"] += flt(d.outstanding_amount)

	# 5. Collect All Relevant Agents
	all_agents = set()
	if agent_filter:
		all_agents.add(agent_filter)
	else:
		all_agents.update(call_map.keys())
		all_agents.update(assignment_map.keys())
		all_agents.update(agent_sales_map.keys())

	user_names = {}
	if all_agents:
		users = frappe.get_all("User", filters={"name": ["in", list(all_agents)]}, fields=["name", "full_name"])
		user_names = {u.name: u.full_name or u.name for u in users}

	# 6. Assemble Output Rows
	data = []
	for agent in sorted(all_agents):
		calls_info = call_map.get(agent, {})
		sales_info = agent_sales_map.get(agent, {
			"doc_count": 0,
			"total_sales": 0.0,
			"paid_amount": 0.0,
			"outstanding_amount": 0.0
		})

		total_calls = calls_info.get("total_calls", 0)
		interested_calls = calls_info.get("interested_calls", 0)
		assigned_cust = assignment_map.get(agent, 0)
		doc_count = sales_info["doc_count"]
		total_sales = flt(sales_info["total_sales"], 2)

		avg_value = flt(total_sales / doc_count, 2) if doc_count > 0 else 0.0
		conversion_rate = flt((doc_count / total_calls) * 100, 1) if total_calls > 0 else 0.0

		row = {
			"agent": agent,
			"agent_name": user_names.get(agent, agent),
			"assigned_customers": assigned_cust,
			"total_calls": total_calls,
			"interested_calls": interested_calls,
			"doc_count": doc_count,
			"total_sales": total_sales,
			"avg_value": avg_value,
			"conversion_rate": conversion_rate
		}

		if doc_type == "Sales Invoice":
			row["paid_amount"] = flt(sales_info["paid_amount"], 2)
			row["outstanding_amount"] = flt(sales_info["outstanding_amount"], 2)

		data.append(row)

	# Sort by total_sales DESC
	data.sort(key=lambda x: x["total_sales"], reverse=True)

	return data


def get_chart(data, filters):
	if not data:
		return None

	doc_type = filters.get("doc_type") or "Sales Invoice"
	labels = [r.get("agent_name") or r.get("agent") for r in data[:10]]

	datasets = [
		{
			"name": _("Total Sales"),
			"values": [r.get("total_sales", 0) for r in data[:10]]
		}
	]

	if doc_type == "Sales Invoice":
		datasets.append({
			"name": _("Paid Amount"),
			"values": [r.get("paid_amount", 0) for r in data[:10]]
		})

	return {
		"data": {
			"labels": labels,
			"datasets": datasets
		},
		"type": "bar",
		"colors": ["#5470C6", "#91CC75"],
		"barOptions": {"stacked": False}
	}


def get_summary(data, filters):
	if not data:
		return []

	doc_type = filters.get("doc_type") or "Sales Invoice"
	doc_type_label = _(doc_type)

	total_sales = sum(r.get("total_sales", 0) for r in data)
	total_docs = sum(r.get("doc_count", 0) for r in data)
	total_calls = sum(r.get("total_calls", 0) for r in data)
	overall_conv = flt((total_docs / total_calls) * 100, 1) if total_calls > 0 else 0.0

	top_agent = data[0].get("agent_name") if data else "-"

	summary = [
		{"label": _("Total Sales Revenue"), "value": total_sales, "indicator": "blue", "datatype": "Currency"},
		{"label": f"{doc_type_label} " + _("Count"), "value": total_docs, "indicator": "green"},
		{"label": _("Top Performing Agent"), "value": top_agent, "indicator": "green"},
		{"label": _("Avg Conversion Rate"), "value": f"{overall_conv}%", "indicator": "orange" if overall_conv < 20 else "green"}
	]

	return summary
