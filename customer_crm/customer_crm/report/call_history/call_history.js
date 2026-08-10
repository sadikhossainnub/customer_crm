// Copyright (c) 2026, Customer CRM and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Call History"] = {
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
			fieldname: "customer",
			label: __("Customer"),
			fieldtype: "Link",
			options: "Customer",
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
			fieldname: "call_direction",
			label: __("Direction"),
			fieldtype: "Select",
			options: ["", "Inbound", "Outbound"],
			reqd: 0,
		},
		{
			fieldname: "call_status",
			label: __("Status"),
			fieldtype: "Select",
			options: ["", "Ringing", "Answered", "Missed", "Completed"],
			reqd: 0,
		},
		{
			fieldname: "call_outcome",
			label: __("Outcome"),
			fieldtype: "Link",
			options: "Call Outcome",
			reqd: 0,
		},
		{
			fieldname: "phone",
			label: __("Phone Number"),
			fieldtype: "Data",
			reqd: 0,
		}
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

		if (column.fieldname === "call_status" && data && data.call_status) {
			const statusColors = {
				"Completed": "#28a745",
				"Answered": "#007bff",
				"Ringing": "#ffc107",
				"Missed": "#dc3545"
			};
			const color = statusColors[data.call_status] || "#6c757d";
			value = `<span class="indicator-pill" style="background-color: ${color}22; color: ${color}; font-weight: bold; padding: 3px 8px; border-radius: 12px; font-size: 11px;">${data.call_status}</span>`;
		}

		if (column.fieldname === "call_direction" && data && data.call_direction) {
			const icon = data.call_direction === "Inbound" ? "📥 Inbound" : "📤 Outbound";
			const color = data.call_direction === "Inbound" ? "#17a2b8" : "#6f42c1";
			value = `<span style="color: ${color}; font-weight: 600;">${icon}</span>`;
		}

		return value;
	}
};
