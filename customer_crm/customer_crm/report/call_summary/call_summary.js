// Copyright (c) 2026, Customer CRM and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Call Summary"] = {
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
			default: frappe.datetime.get_today(),
			reqd: 0,
		},
		{
			fieldname: "agent",
			label: __("Agent"),
			fieldtype: "Link",
			options: "User",
			reqd: 0,
		},
		{
			fieldname: "call_outcome",
			label: __("Call Outcome"),
			fieldtype: "Select",
			options: [
				"",
				"Interested",
				"Not Interested",
				"Follow Up",
				"No Answer",
				"Busy",
				"Wrong Number",
			].join("\n"),
			reqd: 0,
		},
	],

	onload: function (report) {
		report.page.add_inner_button(__("Today"), function () {
			frappe.query_report.set_filter_value("from_date", frappe.datetime.get_today());
			frappe.query_report.set_filter_value("to_date", frappe.datetime.get_today());
			frappe.query_report.refresh();
		});
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
	},

	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (column.fieldname === "day_achievement_pct" && data) {
			let pct = parseFloat(data.day_achievement_pct) || 0;
			let color =
				pct >= 100 ? "#28a745" : pct >= 75 ? "#ffc107" : pct >= 50 ? "#fd7e14" : "#dc3545";
			value = `<span style="color: ${color}; font-weight: bold;">${pct}%</span>`;
		}

		if (column.fieldname === "call_outcome" && data && data.call_outcome) {
			const colorMap = {
				Interested: "#28a745",
				"Not Interested": "#dc3545",
				"Follow Up": "#007bff",
				"No Answer": "#6c757d",
				Busy: "#ffc107",
				"Wrong Number": "#6c757d",
			};
			const color = colorMap[data.call_outcome] || "#333";
			value = `<span style="color: ${color}; font-weight: 500;">${data.call_outcome}</span>`;
		}

		return value;
	},
};
