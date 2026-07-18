frappe.provide('frappe.dashboards.chart_sources');

frappe.dashboards.chart_sources['Customer Call History Trend'] = {
	method: 'customer_crm.customer_crm.dashboard_chart_source.customer_call_history_trend.customer_call_history_trend.get',
	filters: [
		{
			fieldname: 'customer',
			label: __('Customer'),
			fieldtype: 'Link',
			options: 'Customer',
		}
	],
};
