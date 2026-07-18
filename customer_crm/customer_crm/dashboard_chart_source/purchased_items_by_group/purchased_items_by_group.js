frappe.provide('frappe.dashboards.chart_sources');

frappe.dashboards.chart_sources['Purchased Items by Group'] = {
	method: 'customer_crm.customer_crm.dashboard_chart_source.purchased_items_by_group.purchased_items_by_group.get',
	filters: [
		{
			fieldname: 'customer',
			label: __('Customer'),
			fieldtype: 'Link',
			options: 'Customer',
		}
	],
};
