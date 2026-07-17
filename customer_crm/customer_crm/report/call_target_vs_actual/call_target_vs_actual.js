// Copyright (c) 2026, Customer CRM and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Call Target vs Actual"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.month_start(),
			reqd: 0,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.month_end(),
			reqd: 0,
		},
		{
			fieldname: "agent",
			label: __("Agent"),
			fieldtype: "Link",
			options: "User",
			reqd: 0,
		},
	],

	onload: function (report) {
		report.page.add_inner_button(__("This Week"), function () {
			frappe.query_report.set_filter_value("from_date", frappe.datetime.week_start());
			frappe.query_report.set_filter_value("to_date", frappe.datetime.week_end());
			frappe.query_report.refresh();
		});
		report.page.add_inner_button(__("This Month"), function () {
			frappe.query_report.set_filter_value("from_date", frappe.datetime.month_start());
			frappe.query_report.set_filter_value("to_date", frappe.datetime.month_end());
			frappe.query_report.refresh();
		});
		report.page.add_inner_button(__("Today"), function () {
			frappe.query_report.set_filter_value("from_date", frappe.datetime.get_today());
			frappe.query_report.set_filter_value("to_date", frappe.datetime.get_today());
			frappe.query_report.refresh();
		});
	},

	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (column.fieldname === "status") {
			if (data && data.status) {
				if (data.status.includes("On Target")) {
					value = `<span style="color: #28a745; font-weight: bold;">${data.status}</span>`;
				} else if (data.status.includes("Near Target")) {
					value = `<span style="color: #ffc107; font-weight: bold;">${data.status}</span>`;
				} else if (data.status.includes("Below Target")) {
					value = `<span style="color: #fd7e14; font-weight: bold;">${data.status}</span>`;
				} else if (data.status.includes("Critical")) {
					value = `<span style="color: #dc3545; font-weight: bold;">${data.status}</span>`;
				} else {
					value = `<span style="color: #6c757d;">${data.status}</span>`;
				}
			}
		}

		if (column.fieldname === "achievement_pct" && data) {
			let pct = parseFloat(data.achievement_pct) || 0;
			let color = pct >= 100 ? "#28a745" : pct >= 75 ? "#ffc107" : pct >= 50 ? "#fd7e14" : "#dc3545";
			value = `<span style="color: ${color}; font-weight: bold;">${pct}%</span>`;
		}

		return value;
	},
};
