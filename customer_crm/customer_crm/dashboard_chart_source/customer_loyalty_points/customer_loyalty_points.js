frappe.provide('frappe.dashboards.chart_sources');

frappe.dashboards.chart_sources['Customer Loyalty Points'] = {
	method: 'customer_crm.customer_crm.dashboard_chart_source.customer_loyalty_points.customer_loyalty_points.get',
	filters: [
		{
			fieldname: 'customer',
			label: __('Customer'),
			fieldtype: 'Link',
			options: 'Customer',
		}
	],
};
