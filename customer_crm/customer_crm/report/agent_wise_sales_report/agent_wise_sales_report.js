// Copyright (c) 2026, Customer CRM and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Agent Wise Sales Report"] = {
	filters: [
		{
			fieldname: "doc_type",
			label: __("Document Type"),
			fieldtype: "Select",
			options: ["Sales Invoice", "Sales Order", "Delivery Note"],
			default: "Sales Invoice",
			reqd: 1,
			on_change: function () {
				let doc_type = frappe.query_report.get_filter_value("doc_type");
				let status_filter = frappe.query_report.get_filter("status");
				if (!status_filter) return;

				if (doc_type === "Sales Invoice") {
					status_filter.df.options = ["", "Submitted", "Draft", "Paid", "Unpaid", "Overdue", "Cancelled"];
				} else if (doc_type === "Sales Order") {
					status_filter.df.options = ["", "Submitted", "Draft", "To Deliver and Bill", "To Deliver", "To Bill", "Completed", "Cancelled"];
				} else if (doc_type === "Delivery Note") {
					status_filter.df.options = ["", "Submitted", "Draft", "To Bill", "Completed", "Cancelled"];
				}
				status_filter.refresh();
				frappe.query_report.refresh();
			}
		},
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: ["", "Submitted", "Draft", "Paid", "Unpaid", "Overdue", "Cancelled"],
			default: "Submitted",
			reqd: 0,
		},
		{
			fieldname: "date_range_preset",
			label: __("Date Preset"),
			fieldtype: "Select",
			options: ["This Month", "Today", "Yesterday", "This Week", "Last Week", "Last Month", "This Quarter", "This Year", "Custom"],
			default: "This Month",
			on_change: function () {
				let preset = frappe.query_report.get_filter_value("date_range_preset");
				if (!preset || preset === "Custom") return;

				let today = frappe.datetime.get_today();
				let from_date = today;
				let to_date = today;

				if (preset === "Today") {
					from_date = today;
					to_date = today;
				} else if (preset === "Yesterday") {
					from_date = frappe.datetime.add_days(today, -1);
					to_date = frappe.datetime.add_days(today, -1);
				} else if (preset === "This Week") {
					from_date = frappe.datetime.week_start();
					to_date = frappe.datetime.week_end();
				} else if (preset === "Last Week") {
					let last_week_day = frappe.datetime.add_days(today, -7);
					from_date = frappe.datetime.user_to_str(moment(last_week_day).startOf('week').toDate());
					to_date = frappe.datetime.user_to_str(moment(last_week_day).endOf('week').toDate());
				} else if (preset === "This Month") {
					from_date = frappe.datetime.month_start();
					to_date = frappe.datetime.month_end();
				} else if (preset === "Last Month") {
					let last_month_day = frappe.datetime.add_months(today, -1);
					from_date = frappe.datetime.user_to_str(moment(last_month_day).startOf('month').toDate());
					to_date = frappe.datetime.user_to_str(moment(last_month_day).endOf('month').toDate());
				} else if (preset === "This Quarter") {
					from_date = frappe.datetime.user_to_str(moment().startOf('quarter').toDate());
					to_date = frappe.datetime.user_to_str(moment().endOf('quarter').toDate());
				} else if (preset === "This Year") {
					from_date = frappe.datetime.user_to_str(moment().startOf('year').toDate());
					to_date = frappe.datetime.user_to_str(moment().endOf('year').toDate());
				}

				frappe.query_report.set_filter_value("from_date", from_date);
				frappe.query_report.set_filter_value("to_date", to_date);
				frappe.query_report.refresh();
			}
		},
		{
			fieldname: "date_based_on",
			label: __("Date Based On"),
			fieldtype: "Select",
			options: ["Posting/Transaction Date", "Due Date", "Creation Date"],
			default: "Posting/Transaction Date",
			reqd: 0,
		},
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
		{
			fieldname: "customer_group",
			label: __("Customer Group"),
			fieldtype: "Link",
			options: "Customer Group",
			reqd: 0,
		}
	],

	onload: function (report) {
		report.page.add_inner_button(__("This Week"), function () {
			frappe.query_report.set_filter_value("date_range_preset", "This Week");
		});
		report.page.add_inner_button(__("This Month"), function () {
			frappe.query_report.set_filter_value("date_range_preset", "This Month");
		});
		report.page.add_inner_button(__("Today"), function () {
			frappe.query_report.set_filter_value("date_range_preset", "Today");
		});
	},

	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (column.fieldname === "conversion_rate" && data) {
			let pct = parseFloat(data.conversion_rate) || 0;
			let color = pct >= 50 ? "#28a745" : pct >= 20 ? "#17a2b8" : pct >= 10 ? "#ffc107" : "#6c757d";
			value = `<span style="color: ${color}; font-weight: bold;">${pct}%</span>`;
		}

		if (column.fieldname === "total_sales" && data) {
			value = `<span style="font-weight: bold;">${value}</span>`;
		}

		return value;
	}
};
