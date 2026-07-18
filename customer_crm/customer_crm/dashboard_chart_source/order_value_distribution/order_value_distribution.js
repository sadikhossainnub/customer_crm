frappe.provide('frappe.dashboards.chart_sources');

frappe.dashboards.chart_sources['Order Value Distribution'] = {
	method: 'customer_crm.customer_crm.dashboard_chart_source.order_value_distribution.order_value_distribution.get',
	filters: [
		{
			fieldname: 'customer',
			label: __('Customer'),
			fieldtype: 'Link',
			options: 'Customer',
		}
	],
};
