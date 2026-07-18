frappe.provide('frappe.dashboards.chart_sources');

frappe.dashboards.chart_sources['Order Frequency per Month'] = {
	method: 'customer_crm.customer_crm.dashboard_chart_source.order_frequency_per_month.order_frequency_per_month.get',
	filters: [
		{
			fieldname: 'customer',
			label: __('Customer'),
			fieldtype: 'Link',
			options: 'Customer',
		}
	],
};
