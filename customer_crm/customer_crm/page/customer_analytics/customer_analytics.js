frappe.pages["customer-analytics"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "Customer Analytics",
		single_column: true,
	});

	page.main.addClass("customer-analytics-page");

	// Add date range filter
	const from_date = page.add_field({
		fieldname: "from_date",
		label: __("From Date"),
		fieldtype: "Date",
		default: frappe.datetime.add_months(frappe.datetime.get_today(), -12),
		change: () => dashboard.refresh(),
	});

	const to_date = page.add_field({
		fieldname: "to_date",
		label: __("To Date"),
		fieldtype: "Date",
		default: frappe.datetime.get_today(),
		change: () => dashboard.refresh(),
	});

	page.add_inner_button(__("Refresh"), () => dashboard.refresh(), null, "primary");

	const dashboard = new CustomerAnalyticsDashboard(page, from_date, to_date);
	dashboard.refresh();
};

class CustomerAnalyticsDashboard {
	constructor(page, from_date_field, to_date_field) {
		this.page = page;
		this.from_date_field = from_date_field;
		this.to_date_field = to_date_field;
		this.charts = {};
		this.currency = frappe.defaults.get_default("currency") || "BDT";
		this.render_skeleton();
	}

	render_skeleton() {
		this.page.main.html(`
			<div class="analytics-container">
				<!-- Summary Cards -->
				<div class="summary-cards" id="summary-cards">
					<div class="summary-card skeleton-card">
						<div class="skeleton-line"></div>
						<div class="skeleton-line short"></div>
					</div>
					<div class="summary-card skeleton-card">
						<div class="skeleton-line"></div>
						<div class="skeleton-line short"></div>
					</div>
					<div class="summary-card skeleton-card">
						<div class="skeleton-line"></div>
						<div class="skeleton-line short"></div>
					</div>
					<div class="summary-card skeleton-card">
						<div class="skeleton-line"></div>
						<div class="skeleton-line short"></div>
					</div>
					<div class="summary-card skeleton-card">
						<div class="skeleton-line"></div>
						<div class="skeleton-line short"></div>
					</div>
					<div class="summary-card skeleton-card">
						<div class="skeleton-line"></div>
						<div class="skeleton-line short"></div>
					</div>
				</div>

				<!-- Charts Grid -->
				<div class="charts-grid">
					<!-- Row 1: New Customers Trend + Avg Order Value -->
					<div class="chart-card full-width" id="new-customers-chart">
						<div class="chart-header">
							<h3>📈 New Customers Trend</h3>
							<span class="chart-subtitle">Monthly customer acquisition</span>
						</div>
						<div class="chart-body"><div class="chart-loading"><span class="loading-spinner"></span></div></div>
					</div>

					<div class="chart-card half-width" id="customer-revenue-chart">
						<div class="chart-header">
							<h3>💰 Customer-wise Revenue (Top 10)</h3>
							<span class="chart-subtitle">Highest revenue generating customers</span>
						</div>
						<div class="chart-body"><div class="chart-loading"><span class="loading-spinner"></span></div></div>
					</div>

					<div class="chart-card half-width" id="customer-group-chart">
						<div class="chart-header">
							<h3>🏷️ Customer Group-wise Sales</h3>
							<span class="chart-subtitle">Retail vs Wholesale distribution</span>
						</div>
						<div class="chart-body"><div class="chart-loading"><span class="loading-spinner"></span></div></div>
					</div>

					<div class="chart-card half-width" id="territory-chart">
						<div class="chart-header">
							<h3>🗺️ Territory-wise Sales</h3>
							<span class="chart-subtitle">Sales distribution across territories</span>
						</div>
						<div class="chart-body"><div class="chart-loading"><span class="loading-spinner"></span></div></div>
					</div>

					<div class="chart-card half-width" id="repeat-new-chart">
						<div class="chart-header">
							<h3>🔄 Repeat vs New Customers</h3>
							<span class="chart-subtitle">Customer retention ratio</span>
						</div>
						<div class="chart-body"><div class="chart-loading"><span class="loading-spinner"></span></div></div>
					</div>

					<div class="chart-card full-width" id="avg-order-chart">
						<div class="chart-header">
							<h3>📊 Average Order Value Trend</h3>
							<span class="chart-subtitle">Monthly average order value</span>
						</div>
						<div class="chart-body"><div class="chart-loading"><span class="loading-spinner"></span></div></div>
					</div>

					<!-- CLV Table -->
					<div class="chart-card full-width" id="clv-table">
						<div class="chart-header">
							<h3>⭐ Customer Lifetime Value (CLV)</h3>
							<span class="chart-subtitle">Top 20 customers by total lifetime revenue</span>
						</div>
						<div class="chart-body table-body"><div class="chart-loading"><span class="loading-spinner"></span></div></div>
					</div>

					<!-- Loyalty Points -->
					<div class="chart-card half-width" id="loyalty-table">
						<div class="chart-header">
							<h3>🎁 Loyalty Points Balance</h3>
							<span class="chart-subtitle">Customer loyalty program status</span>
						</div>
						<div class="chart-body table-body"><div class="chart-loading"><span class="loading-spinner"></span></div></div>
					</div>

					<!-- Inactive Customers -->
					<div class="chart-card half-width" id="inactive-table">
						<div class="chart-header">
							<h3>⚠️ Inactive / Churned Customers</h3>
							<span class="chart-subtitle">No orders in last 90 days</span>
						</div>
						<div class="chart-body table-body"><div class="chart-loading"><span class="loading-spinner"></span></div></div>
					</div>

					<!-- Section Divider -->
					<div class="section-divider full-width">
						<h2 class="section-title">📋 Sales & Payment Analysis</h2>
					</div>

					<div class="chart-card full-width" id="sales-trend-chart">
						<div class="chart-header">
							<h3>📈 Sales Trend (Monthly)</h3>
							<span class="chart-subtitle">Monthly revenue from Sales Invoices</span>
						</div>
						<div class="chart-body"><div class="chart-loading"><span class="loading-spinner"></span></div></div>
					</div>

					<div class="chart-card half-width" id="outstanding-paid-chart">
						<div class="chart-header">
							<h3>💳 Outstanding vs Paid</h3>
							<span class="chart-subtitle">Receivable status breakdown</span>
						</div>
						<div class="chart-body"><div class="chart-loading"><span class="loading-spinner"></span></div></div>
					</div>

					<div class="chart-card half-width" id="payment-behavior-chart">
						<div class="chart-header">
							<h3>⏱️ Payment Behavior</h3>
							<span class="chart-subtitle">On-time vs late payment ratio</span>
						</div>
						<div class="chart-body"><div class="chart-loading"><span class="loading-spinner"></span></div></div>
					</div>

					<div class="chart-card full-width" id="top-items-chart">
						<div class="chart-header">
							<h3>🏆 Top Selling Items</h3>
							<span class="chart-subtitle">Item-wise sales by amount</span>
						</div>
						<div class="chart-body"><div class="chart-loading"><span class="loading-spinner"></span></div></div>
					</div>

					<div class="chart-card half-width" id="order-distribution-chart">
						<div class="chart-header">
							<h3>📊 Order Value Distribution</h3>
							<span class="chart-subtitle">Order size pattern (histogram)</span>
						</div>
						<div class="chart-body"><div class="chart-loading"><span class="loading-spinner"></span></div></div>
					</div>

					<div class="chart-card half-width" id="credit-limit-chart">
						<div class="chart-header">
							<h3>🔋 Credit Limit Utilization</h3>
							<span class="chart-subtitle">Top customers by credit usage</span>
						</div>
						<div class="chart-body"><div class="chart-loading"><span class="loading-spinner"></span></div></div>
					</div>
				</div>
			</div>
		`);
	}

	refresh() {
		const from_date = this.from_date_field?.get_value() ||
			frappe.datetime.add_months(frappe.datetime.get_today(), -12);
		const to_date = this.to_date_field?.get_value() || frappe.datetime.get_today();

		frappe.call({
			method: "customer_crm.customer_crm.page.customer_analytics.customer_analytics.get_dashboard_data",
			args: { from_date, to_date },
			callback: (r) => {
				if (r.message) {
					this.render_all(r.message);
				}
			},
			error: () => {
				frappe.msgprint(__("Failed to load dashboard data. Please try again."));
			},
		});
	}

	render_all(data) {
		this.render_summary_cards(data.summary_cards);
		this.render_new_customers_trend(data.new_customers_trend);
		this.render_customer_revenue(data.customer_wise_revenue);
		this.render_customer_group_sales(data.customer_group_sales);
		this.render_territory_sales(data.territory_sales);
		this.render_repeat_vs_new(data.repeat_vs_new);
		this.render_avg_order_trend(data.avg_order_value_trend);
		this.render_clv_table(data.customer_lifetime_value);
		this.render_loyalty_table(data.loyalty_points);
		this.render_inactive_table(data.inactive_customers);
		this.render_sales_trend(data.sales_trend_monthly);
		this.render_outstanding_vs_paid(data.outstanding_vs_paid);
		this.render_top_selling_items(data.top_selling_items);
		this.render_order_distribution(data.order_value_distribution);
		this.render_payment_behavior(data.payment_behavior);
		this.render_credit_limit(data.credit_limit_utilization);
	}

	render_summary_cards(data) {
		if (!data) return;
		const container = document.getElementById("summary-cards");
		container.innerHTML = `
			<div class="summary-card">
				<div class="card-icon" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
					<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
				</div>
				<div class="card-content">
					<span class="card-label">Total Customers</span>
					<span class="card-value">${format_number(data.total_customers)}</span>
				</div>
			</div>
			<div class="summary-card">
				<div class="card-icon" style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);">
					<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="8.5" cy="7" r="4"/><line x1="20" y1="8" x2="20" y2="14"/><line x1="23" y1="11" x2="17" y2="11"/></svg>
				</div>
				<div class="card-content">
					<span class="card-label">New Customers</span>
					<span class="card-value">${format_number(data.new_customers)}</span>
				</div>
			</div>
			<div class="summary-card">
				<div class="card-icon" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
					<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
				</div>
				<div class="card-content">
					<span class="card-label">Total Revenue</span>
					<span class="card-value">${format_currency(data.total_revenue, this.currency)}</span>
				</div>
			</div>
			<div class="summary-card">
				<div class="card-icon" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
					<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><rect x="1" y="4" width="22" height="16" rx="2" ry="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg>
				</div>
				<div class="card-content">
					<span class="card-label">Total Orders</span>
					<span class="card-value">${format_number(data.total_orders)}</span>
				</div>
			</div>
			<div class="summary-card">
				<div class="card-icon" style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);">
					<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
				</div>
				<div class="card-content">
					<span class="card-label">Avg Order Value</span>
					<span class="card-value">${format_currency(data.avg_order_value, this.currency)}</span>
				</div>
			</div>
			<div class="summary-card">
				<div class="card-icon" style="background: linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%);">
					<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
				</div>
				<div class="card-content">
					<span class="card-label">Active Customers (90d)</span>
					<span class="card-value">${format_number(data.active_customers)}</span>
				</div>
			</div>
		`;
	}

	render_new_customers_trend(data) {
		const container = this.get_chart_container("new-customers-chart");
		if (!data || !data.length) {
			container.innerHTML = this.empty_state("No customer data found for the selected period");
			return;
		}

		const labels = data.map((d) => this.format_month_label(d.month));
		const values = data.map((d) => d.count);

		this.destroy_chart("new-customers-chart");
		this.charts["new-customers-chart"] = new frappe.Chart(container, {
			type: "line",
			height: 280,
			colors: ["#667eea"],
			data: {
				labels: labels,
				datasets: [{ name: "New Customers", values: values }],
			},
			lineOptions: { regionFill: 1, hideDots: 0, spline: 1 },
			axisOptions: { xIsSeries: true },
			tooltipOptions: {
				formatTooltipY: (d) => d + " customers",
			},
		});
	}

	render_customer_revenue(data) {
		const container = this.get_chart_container("customer-revenue-chart");
		if (!data || !data.length) {
			container.innerHTML = this.empty_state("No revenue data found");
			return;
		}

		const labels = data.map((d) => d.customer_name || d.customer);
		const values = data.map((d) => d.total_revenue);
		const currency = this.currency;

		this.destroy_chart("customer-revenue-chart");
		this.charts["customer-revenue-chart"] = new frappe.Chart(container, {
			type: "bar",
			height: 300,
			colors: ["#764ba2"],
			data: {
				labels: labels,
				datasets: [{ name: "Revenue", values: values }],
			},
			barOptions: { spaceRatio: 0.4 },
			tooltipOptions: {
				formatTooltipY: (d) => format_currency(d, currency),
			},
		});
	}

	render_customer_group_sales(data) {
		const container = this.get_chart_container("customer-group-chart");
		if (!data || !data.length) {
			container.innerHTML = this.empty_state("No customer group data found");
			return;
		}

		const labels = data.map((d) => d.customer_group);
		const values = data.map((d) => d.total_sales);
		const currency = this.currency;

		this.destroy_chart("customer-group-chart");
		this.charts["customer-group-chart"] = new frappe.Chart(container, {
			type: "pie",
			height: 300,
			colors: ["#667eea", "#764ba2", "#f5576c", "#11998e", "#fa709a", "#4facfe", "#38ef7d", "#fee140"],
			data: {
				labels: labels,
				datasets: [{ values: values }],
			},
			tooltipOptions: {
				formatTooltipY: (d) => format_currency(d, currency),
			},
		});
	}

	render_territory_sales(data) {
		const container = this.get_chart_container("territory-chart");
		if (!data || !data.length) {
			container.innerHTML = this.empty_state("No territory data found");
			return;
		}

		const labels = data.map((d) => d.territory);
		const values = data.map((d) => d.total_sales);
		const currency = this.currency;

		this.destroy_chart("territory-chart");
		this.charts["territory-chart"] = new frappe.Chart(container, {
			type: "percentage",
			height: 300,
			colors: ["#11998e", "#667eea", "#f5576c", "#fa709a", "#4facfe", "#764ba2", "#fee140", "#38ef7d"],
			data: {
				labels: labels,
				datasets: [{ values: values }],
			},
			tooltipOptions: {
				formatTooltipY: (d) => format_currency(d, currency),
			},
		});
	}

	render_repeat_vs_new(data) {
		const container = this.get_chart_container("repeat-new-chart");
		if (!data || data.total === 0) {
			container.innerHTML = this.empty_state("No order data to calculate ratio");
			return;
		}

		this.destroy_chart("repeat-new-chart");

		const new_pct = data.total > 0 ? ((data.new / data.total) * 100).toFixed(1) : 0;
		const repeat_pct = data.total > 0 ? ((data.repeat / data.total) * 100).toFixed(1) : 0;

		container.innerHTML = `
			<div class="ratio-display">
				<div class="ratio-visual">
					<div class="ratio-ring">
						<svg viewBox="0 0 200 200" class="ratio-svg">
							<circle cx="100" cy="100" r="80" fill="none" stroke="var(--border-color, #e2e8f0)" stroke-width="16"/>
							<circle cx="100" cy="100" r="80" fill="none" stroke="#11998e" stroke-width="16"
								stroke-dasharray="${(data.repeat / data.total) * 502.65} 502.65"
								stroke-dashoffset="0" transform="rotate(-90 100 100)"
								style="transition: stroke-dasharray 1s ease;"/>
							<circle cx="100" cy="100" r="80" fill="none" stroke="#667eea" stroke-width="16"
								stroke-dasharray="${(data.new / data.total) * 502.65} 502.65"
								stroke-dashoffset="${-(data.repeat / data.total) * 502.65}"
								transform="rotate(-90 100 100)"
								style="transition: stroke-dasharray 1s ease;"/>
						</svg>
						<div class="ratio-center-text">
							<span class="ratio-total">${data.total}</span>
							<span class="ratio-label">Total</span>
						</div>
					</div>
				</div>
				<div class="ratio-legend">
					<div class="legend-item">
						<span class="legend-dot" style="background: #11998e;"></span>
						<div class="legend-info">
							<span class="legend-label">Repeat Customers</span>
							<span class="legend-value">${data.repeat} (${repeat_pct}%)</span>
						</div>
					</div>
					<div class="legend-item">
						<span class="legend-dot" style="background: #667eea;"></span>
						<div class="legend-info">
							<span class="legend-label">New Customers</span>
							<span class="legend-value">${data.new} (${new_pct}%)</span>
						</div>
					</div>
				</div>
			</div>
		`;
	}

	render_avg_order_trend(data) {
		const container = this.get_chart_container("avg-order-chart");
		if (!data || !data.length) {
			container.innerHTML = this.empty_state("No order data found for the selected period");
			return;
		}

		const labels = data.map((d) => this.format_month_label(d.month));
		const avg_values = data.map((d) => d.avg_value);
		const revenue_values = data.map((d) => d.total_revenue);
		const currency = this.currency;

		this.destroy_chart("avg-order-chart");
		this.charts["avg-order-chart"] = new frappe.Chart(container, {
			type: "axis-mixed",
			height: 280,
			colors: ["#f5576c", "#667eea"],
			data: {
				labels: labels,
				datasets: [
					{ name: "Avg Order Value", values: avg_values, chartType: "line" },
					{ name: "Total Revenue", values: revenue_values, chartType: "bar" },
				],
			},
			lineOptions: { spline: 1 },
			barOptions: { spaceRatio: 0.4 },
			tooltipOptions: {
				formatTooltipY: (d) => format_currency(d, currency),
			},
		});
	}

	render_clv_table(data) {
		const container = this.get_chart_container("clv-table");
		if (!data || !data.length) {
			container.innerHTML = this.empty_state("No CLV data available");
			return;
		}

		let rows = data
			.map(
				(d, i) => `
			<tr>
				<td><span class="rank-badge rank-${i < 3 ? "top" : "normal"}">${i + 1}</span></td>
				<td><a href="/app/customer/${d.customer}" class="customer-link">${d.customer_name || d.customer}</a></td>
				<td>${d.customer_group || "-"}</td>
				<td class="text-right font-bold">${format_currency(d.lifetime_value, this.currency)}</td>
				<td class="text-right">${d.total_orders}</td>
				<td class="text-right">${format_currency(d.avg_order_value, this.currency)}</td>
				<td>${d.first_order || "-"}</td>
				<td>${d.last_order || "-"}</td>
				<td class="text-right">${d.customer_age_days || 0} days</td>
			</tr>
		`
			)
			.join("");

		container.innerHTML = `
			<div class="analytics-table-wrapper">
				<table class="analytics-table">
					<thead>
						<tr>
							<th>#</th>
							<th>Customer</th>
							<th>Group</th>
							<th class="text-right">Lifetime Value</th>
							<th class="text-right">Orders</th>
							<th class="text-right">Avg Order</th>
							<th>First Order</th>
							<th>Last Order</th>
							<th class="text-right">Customer Age</th>
						</tr>
					</thead>
					<tbody>${rows}</tbody>
				</table>
			</div>
		`;
	}

	render_loyalty_table(data) {
		const container = this.get_chart_container("loyalty-table");
		if (!data || !data.length) {
			container.innerHTML = this.empty_state("No loyalty points data available. Loyalty program may not be active.");
			return;
		}

		let rows = data
			.map(
				(d) => `
			<tr>
				<td><a href="/app/customer/${d.customer}" class="customer-link">${d.customer_name || d.customer}</a></td>
				<td class="text-right">
					<span class="points-badge">${format_number(d.points_balance)} pts</span>
				</td>
				<td>${d.last_activity || "-"}</td>
			</tr>
		`
			)
			.join("");

		container.innerHTML = `
			<div class="analytics-table-wrapper">
				<table class="analytics-table compact">
					<thead>
						<tr>
							<th>Customer</th>
							<th class="text-right">Points Balance</th>
							<th>Last Activity</th>
						</tr>
					</thead>
					<tbody>${rows}</tbody>
				</table>
			</div>
		`;
	}

	render_inactive_table(data) {
		const container = this.get_chart_container("inactive-table");
		if (!data || !data.length) {
			container.innerHTML = this.empty_state("🎉 No churned customers! All customers are active.");
			return;
		}

		let rows = data
			.map(
				(d) => `
			<tr>
				<td><a href="/app/customer/${d.customer}" class="customer-link">${d.customer_name || d.customer}</a></td>
				<td>${d.customer_group || "-"}</td>
				<td>${d.last_transaction_date || "-"}</td>
				<td class="text-right">
					<span class="days-badge ${d.days_since_last_order > 180 ? "critical" : "warning"}">
						${d.days_since_last_order} days
					</span>
				</td>
				<td class="text-right">${d.total_orders}</td>
				<td class="text-right">${format_currency(d.total_spent, this.currency)}</td>
			</tr>
		`
			)
			.join("");

		container.innerHTML = `
			<div class="analytics-table-wrapper">
				<table class="analytics-table compact">
					<thead>
						<tr>
							<th>Customer</th>
							<th>Group</th>
							<th>Last Order Date</th>
							<th class="text-right">Days Inactive</th>
							<th class="text-right">Total Orders</th>
							<th class="text-right">Total Spent</th>
						</tr>
					</thead>
					<tbody>${rows}</tbody>
				</table>
			</div>
		`;
	}

	render_sales_trend(data) {
		const container = this.get_chart_container("sales-trend-chart");
		if (!data || !data.length) {
			container.innerHTML = this.empty_state("No sales invoice data found for the selected period");
			return;
		}

		const labels = data.map((d) => this.format_month_label(d.month));
		const values = data.map((d) => d.total_sales);
		const invoice_counts = data.map((d) => d.invoice_count);
		const currency = this.currency;

		this.destroy_chart("sales-trend-chart");
		this.charts["sales-trend-chart"] = new frappe.Chart(container, {
			type: "line",
			height: 280,
			colors: ["#38ef7d"],
			data: {
				labels: labels,
				datasets: [
					{ name: "Total Sales", values: values },
				],
			},
			lineOptions: { regionFill: 1, hideDots: 0, spline: 1 },
			axisOptions: { xIsSeries: true },
			tooltipOptions: {
				formatTooltipY: (d) => format_currency(d, currency),
			},
		});
	}

	render_outstanding_vs_paid(data) {
		const container = this.get_chart_container("outstanding-paid-chart");
		if (!data || data.total_invoiced === 0) {
			container.innerHTML = this.empty_state("No sales invoices found to calculate outstanding status");
			return;
		}

		const labels = ["Paid Amount", "Outstanding Amount"];
		const values = [data.total_paid, data.total_outstanding];
		const currency = this.currency;

		this.destroy_chart("outstanding-paid-chart");
		this.charts["outstanding-paid-chart"] = new frappe.Chart(container, {
			type: "donut",
			height: 300,
			colors: ["#2ecc71", "#e74c3c"],
			data: {
				labels: labels,
				datasets: [{ values: values }],
			},
			tooltipOptions: {
				formatTooltipY: (d) => format_currency(d, currency),
			},
		});
	}

	render_payment_behavior(data) {
		const container = this.get_chart_container("payment-behavior-chart");
		if (!data || data.total === 0) {
			container.innerHTML = this.empty_state("No payment history to analyze behavior");
			return;
		}

		const labels = ["On-time", "Late", "Unpaid"];
		const values = [data.on_time, data.late, data.unpaid];

		this.destroy_chart("payment-behavior-chart");
		this.charts["payment-behavior-chart"] = new frappe.Chart(container, {
			type: "pie",
			height: 300,
			colors: ["#2ecc71", "#f39c12", "#e74c3c"],
			data: {
				labels: labels,
				datasets: [{ values: values }],
			},
			tooltipOptions: {
				formatTooltipY: (d) => d + " invoices",
			},
		});
	}

	render_top_selling_items(data) {
		const container = this.get_chart_container("top-items-chart");
		if (!data || !data.length) {
			container.innerHTML = this.empty_state("No item sales data found");
			return;
		}

		const labels = data.map((d) => d.item_name || d.item_code);
		const values = data.map((d) => d.total_amount);
		const currency = this.currency;

		this.destroy_chart("top-items-chart");
		this.charts["top-items-chart"] = new frappe.Chart(container, {
			type: "bar",
			height: 300,
			colors: ["#4facfe"],
			data: {
				labels: labels,
				datasets: [{ name: "Sales Amount", values: values }],
			},
			barOptions: { spaceRatio: 0.4 },
			tooltipOptions: {
				formatTooltipY: (d) => format_currency(d, currency),
			},
		});
	}

	render_order_distribution(data) {
		const container = this.get_chart_container("order-distribution-chart");
		if (!data || !data.length) {
			container.innerHTML = this.empty_state("No order distribution pattern available");
			return;
		}

		const labels = data.map((d) => d.bucket);
		const values = data.map((d) => d.count);

		this.destroy_chart("order-distribution-chart");
		this.charts["order-distribution-chart"] = new frappe.Chart(container, {
			type: "bar",
			height: 300,
			colors: ["#a18cd1"],
			data: {
				labels: labels,
				datasets: [{ name: "Number of Orders", values: values }],
			},
			barOptions: { spaceRatio: 0.2 },
			tooltipOptions: {
				formatTooltipY: (d) => d + " orders",
			},
		});
	}

	render_credit_limit(data) {
		const container = this.get_chart_container("credit-limit-chart");
		if (!data || !data.length) {
			container.innerHTML = this.empty_state("No credit limits set for any active customer");
			return;
		}

		let rows = data.map((d) => {
			let color_class = "success";
			if (d.utilization_pct > 80) color_class = "danger";
			else if (d.utilization_pct > 50) color_class = "warning";

			return `
				<div class="credit-limit-row">
					<div class="credit-limit-info">
						<a href="/app/customer/${d.customer}" class="customer-link font-bold">${d.customer_name || d.customer}</a>
						<span class="credit-limit-values">
							<strong>${format_currency(d.current_outstanding, this.currency)}</strong> / ${format_currency(d.credit_limit, this.currency)}
						</span>
					</div>
					<div class="credit-limit-bar-wrapper">
						<div class="credit-limit-bar ${color_class}" style="width: ${d.utilization_pct}%"></div>
					</div>
					<span class="credit-limit-pct font-bold ${color_class}">${d.utilization_pct}%</span>
				</div>
			`;
		}).join("");

		container.innerHTML = `
			<div class="credit-limit-container">
				${rows}
			</div>
		`;
	}

	// Helpers
	get_chart_container(id) {
		return document.querySelector(`#${id} .chart-body`);
	}

	destroy_chart(id) {
		if (this.charts[id]) {
			this.charts[id].destroy();
			delete this.charts[id];
		}
	}

	format_month_label(month_str) {
		if (!month_str) return "";
		const [year, month] = month_str.split("-");
		const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
		return `${months[parseInt(month) - 1]} ${year}`;
	}

	empty_state(message) {
		return `
			<div class="empty-state">
				<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" stroke-width="1.5">
					<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
				</svg>
				<p>${message}</p>
			</div>
		`;
	}
}
