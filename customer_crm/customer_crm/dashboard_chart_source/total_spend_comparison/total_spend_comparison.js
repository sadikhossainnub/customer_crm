frappe.provide('frappe.dashboards.chart_sources');

frappe.dashboards.chart_sources['Total Spend Month Wise Comparison'] = {
	method: 'customer_crm.customer_crm.dashboard_chart_source.total_spend_comparison.total_spend_comparison.get',
	filters: [
		{
			fieldname: 'customer',
			label: __('Customer'),
			fieldtype: 'Link',
			options: 'Customer',
		}
	],
};
