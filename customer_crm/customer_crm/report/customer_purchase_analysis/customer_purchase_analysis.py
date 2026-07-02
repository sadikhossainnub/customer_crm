import frappe
from frappe import _


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{
			"label": _("Customer"),
			"fieldname": "customer",
			"fieldtype": "Link",
			"options": "Customer",
			"width": 150
		},
		{
			"label": _("Customer Name"),
			"fieldname": "customer_name",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"label": _("Customer Group"),
			"fieldname": "customer_group",
			"fieldtype": "Link",
			"options": "Customer Group",
			"width": 120
		},
		{
			"label": _("Item Code"),
			"fieldname": "item_code",
			"fieldtype": "Link",
			"options": "Item",
			"width": 120
		},
		{
			"label": _("Item Name"),
			"fieldname": "item_name",
			"fieldtype": "Data",
			"width": 180
		},
		{
			"label": _("Qty Purchased"),
			"fieldname": "qty",
			"fieldtype": "Float",
			"width": 100
		},
		{
			"label": _("Avg Rate"),
			"fieldname": "avg_rate",
			"fieldtype": "Currency",
			"options": "Currency",
			"width": 100
		},
		{
			"label": _("Total Amount"),
			"fieldname": "amount",
			"fieldtype": "Currency",
			"options": "Currency",
			"width": 120
		},
		{
			"label": _("First Purchase Date"),
			"fieldname": "first_purchase_date",
			"fieldtype": "Date",
			"width": 130
		},
		{
			"label": _("Last Purchase Date"),
			"fieldname": "last_purchase_date",
			"fieldtype": "Date",
			"width": 130
		}
	]


def get_data(filters):
	conditions = []
	values = {}

	if filters.get("customer"):
		conditions.append("si.customer = %(customer)s")
		values["customer"] = filters.get("customer")

	if filters.get("customer_group"):
		conditions.append("c.customer_group = %(customer_group)s")
		values["customer_group"] = filters.get("customer_group")

	if filters.get("item_code"):
		conditions.append("sii.item_code = %(item_code)s")
		values["item_code"] = filters.get("item_code")

	if filters.get("from_date"):
		conditions.append("si.posting_date >= %(from_date)s")
		values["from_date"] = filters.get("from_date")

	if filters.get("to_date"):
		conditions.append("si.posting_date <= %(to_date)s")
		values["to_date"] = filters.get("to_date")

	where_clause = " AND ".join(conditions)
	if where_clause:
		where_clause = " AND " + where_clause

	return frappe.db.sql(f"""
		SELECT 
			si.customer,
			si.customer_name,
			c.customer_group,
			sii.item_code,
			sii.item_name,
			SUM(sii.qty) as qty,
			ROUND(SUM(sii.amount) / SUM(sii.qty), 2) as avg_rate,
			SUM(sii.amount) as amount,
			MIN(si.posting_date) as first_purchase_date,
			MAX(si.posting_date) as last_purchase_date
		FROM `tabSales Invoice Item` sii
		INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
		LEFT JOIN `tabCustomer` c ON si.customer = c.name
		WHERE si.docstatus = 1 {where_clause}
		GROUP BY si.customer, sii.item_code
		ORDER BY si.customer_name, SUM(sii.amount) DESC
	""", values, as_dict=1)
