frappe.provide('frappe.dashboards.chart_sources');

frappe.dashboards.chart_sources['Credit Limit Utilization'] = {
	method: 'customer_crm.customer_crm.dashboard_chart_source.credit_limit_utilization.credit_limit_utilization.get',
	filters: [
		{
			fieldname: 'customer',
			label: __('Customer'),
			fieldtype: 'Link',
			options: 'Customer',
		}
	],
};
