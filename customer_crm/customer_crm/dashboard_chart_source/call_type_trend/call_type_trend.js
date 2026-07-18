frappe.provide('frappe.dashboards.chart_sources');

frappe.dashboards.chart_sources['Call Type Trend'] = {
	method: 'customer_crm.customer_crm.dashboard_chart_source.call_type_trend.call_type_trend.get',
	filters: [
		{
			fieldname: 'customer',
			label: __('Customer'),
			fieldtype: 'Link',
			options: 'Customer',
		}
	],
};
