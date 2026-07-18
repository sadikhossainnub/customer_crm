frappe.provide('frappe.dashboards.chart_sources');

frappe.dashboards.chart_sources['Order Trend Graph'] = {
	method: 'customer_crm.customer_crm.dashboard_chart_source.order_trend_graph.order_trend_graph.get',
	filters: [
		{
			fieldname: 'customer',
			label: __('Customer'),
			fieldtype: 'Link',
			options: 'Customer',
		}
	],
};
