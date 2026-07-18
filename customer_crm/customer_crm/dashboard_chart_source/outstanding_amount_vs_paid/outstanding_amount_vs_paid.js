frappe.provide('frappe.dashboards.chart_sources');

frappe.dashboards.chart_sources['Outstanding Amount vs Paid'] = {
	method: 'customer_crm.customer_crm.dashboard_chart_source.outstanding_amount_vs_paid.outstanding_amount_vs_paid.get',
	filters: [
		{
			fieldname: 'customer',
			label: __('Customer'),
			fieldtype: 'Link',
			options: 'Customer',
		}
	],
};
