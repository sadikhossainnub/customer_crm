frappe.provide('frappe.dashboards.chart_sources');

frappe.dashboards.chart_sources['Target vs Achievement'] = {
	method: 'customer_crm.customer_crm.dashboard_chart_source.target_vs_achievement.target_vs_achievement.get',
	filters: [
		{
			fieldname: 'agent',
			label: __('Agent'),
			fieldtype: 'Link',
			options: 'User',
		},
		{
			fieldname: 'from_date',
			label: __('From Date'),
			fieldtype: 'Date',
		},
		{
			fieldname: 'to_date',
			label: __('To Date'),
			fieldtype: 'Date',
		}
	],
};
