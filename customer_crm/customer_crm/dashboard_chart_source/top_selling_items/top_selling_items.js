frappe.provide("frappe.dashboards.chart_sources");

frappe.dashboards.chart_sources["Top Selling Items"] = {
	method: "customer_crm.customer_crm.dashboard_chart_source.top_selling_items.top_selling_items.get",
	filters: [
		{
			fieldname: "customer",
			label: __("Customer"),
			fieldtype: "Link",
			options: "Customer",
		}
	],
};
