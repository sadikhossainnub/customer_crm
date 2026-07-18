frappe.provide('frappe.dashboards.chart_sources');

frappe.dashboards.chart_sources['UTM Source Chart'] = {
	method: 'customer_crm.customer_crm.dashboard_chart_source.utm_source_chart.utm_source_chart.get',
	filters: [
		{
			fieldname: 'customer',
			label: __('Customer'),
			fieldtype: 'Link',
			options: 'Customer',
		}
	],
};
