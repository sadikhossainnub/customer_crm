frappe.provide('frappe.dashboards.chart_sources');

frappe.dashboards.chart_sources['Sales Trend (Monthly)'] = {
	method: 'customer_crm.customer_crm.dashboard_chart_source.sales_trend_(monthly).sales_trend_(monthly).get',
	filters: [
		{
			fieldname: 'customer',
			label: __('Customer'),
			fieldtype: 'Link',
			options: 'Customer',
		}
	],
};
