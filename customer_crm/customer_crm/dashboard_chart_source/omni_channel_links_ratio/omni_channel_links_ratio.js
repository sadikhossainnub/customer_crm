frappe.provide('frappe.dashboards.chart_sources');

frappe.dashboards.chart_sources['Omni Channel Links Ratio'] = {
	method: 'customer_crm.customer_crm.dashboard_chart_source.omni_channel_links_ratio.omni_channel_links_ratio.get',
	filters: [
		{
			fieldname: 'customer',
			label: __('Customer'),
			fieldtype: 'Link',
			options: 'Customer',
		}
	],
};
