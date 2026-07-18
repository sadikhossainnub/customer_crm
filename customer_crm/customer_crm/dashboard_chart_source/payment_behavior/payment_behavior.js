frappe.provide('frappe.dashboards.chart_sources');

frappe.dashboards.chart_sources['Payment Behavior'] = {
	method: 'customer_crm.customer_crm.dashboard_chart_source.payment_behavior.payment_behavior.get',
	filters: [
		{
			fieldname: 'customer',
			label: __('Customer'),
			fieldtype: 'Link',
			options: 'Customer',
		}
	],
};
