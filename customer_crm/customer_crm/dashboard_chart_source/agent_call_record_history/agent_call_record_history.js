frappe.provide('frappe.dashboards.chart_sources');

frappe.dashboards.chart_sources['Agent Call Record History'] = {
	method: 'customer_crm.customer_crm.dashboard_chart_source.agent_call_record_history.agent_call_record_history.get',
	filters: [
		{
			fieldname: 'customer',
			label: __('Customer'),
			fieldtype: 'Link',
			options: 'Customer',
		}
	],
};
