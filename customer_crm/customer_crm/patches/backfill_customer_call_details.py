import frappe


def execute():
	# Get all unique customers with calls
	customers = frappe.get_all("Customer Call", fields=["customer"], distinct=True)

	for c in customers:
		if not c.customer:
			continue

		# Get latest call
		latest_calls = frappe.get_all(
			"Customer Call",
			filters={"customer": c.customer},
			fields=["call_date", "next_follow_up_date"],
			order_by="call_date desc, creation desc",
			limit=1
		)
		if latest_calls:
			latest_call = latest_calls[0]
			frappe.db.set_value("Customer", c.customer, {
				"last_call_date": latest_call.call_date,
				"next_follow_up": latest_call.next_follow_up_date
			}, update_modified=False)

	frappe.db.commit()
	print("Backfilled customer call details for existing customers.")
