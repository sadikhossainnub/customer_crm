frappe.provide('frappe.dashboards.chart_sources');

frappe.dashboards.chart_sources['Total Address and Contact'] = {
	method: 'customer_crm.customer_crm.dashboard_chart_source.total_address_and_contact.total_address_and_contact.get',
	filters: [
		{
			fieldname: 'customer',
			label: __('Customer'),
			fieldtype: 'Link',
			options: 'Customer',
		}
	],
};
