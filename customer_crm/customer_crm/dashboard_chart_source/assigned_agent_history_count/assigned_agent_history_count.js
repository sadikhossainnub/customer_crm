frappe.provide('frappe.dashboards.chart_sources');

frappe.dashboards.chart_sources['Assigned Agent History Count'] = {
	method: 'customer_crm.customer_crm.dashboard_chart_source.assigned_agent_history_count.assigned_agent_history_count.get',
	filters: [
		{
			fieldname: 'customer',
			label: __('Customer'),
			fieldtype: 'Link',
			options: 'Customer',
		}
	],
};
