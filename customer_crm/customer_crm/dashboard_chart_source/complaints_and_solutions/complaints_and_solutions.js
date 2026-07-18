frappe.provide('frappe.dashboards.chart_sources');

frappe.dashboards.chart_sources['Complaints and Solution History'] = {
	method: 'customer_crm.customer_crm.dashboard_chart_source.complaints_and_solutions.complaints_and_solutions.get',
	filters: [
		{
			fieldname: 'customer',
			label: __('Customer'),
			fieldtype: 'Link',
			options: 'Customer',
		}
	],
};
