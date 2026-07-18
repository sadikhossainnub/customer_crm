frappe.provide('frappe.dashboards.chart_sources');

frappe.dashboards.chart_sources['Website Account Status'] = {
	method: 'customer_crm.customer_crm.dashboard_chart_source.website_account_status.website_account_status.get',
	filters: [
		{
			fieldname: 'customer',
			label: __('Customer'),
			fieldtype: 'Link',
			options: 'Customer',
		}
	],
};
