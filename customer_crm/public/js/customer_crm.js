// Customer CRM — Global Realtime Event Listeners
// Handles incoming call screen pops and unmatched call alerts from Asterisk PBX

frappe.realtime.on("incoming_call_popup", (data) => {
	let msg = data.customer
		? `📞 Call from <b>${data.customer}</b> (${data.number})`
		: `📞 Unknown number calling: ${data.number}`;
	frappe.show_alert({message: msg, indicator: 'orange'}, 15);
	if (data.customer) {
		// Optional: auto-open new Customer Call form pre-filled
	}
});

frappe.realtime.on("unmatched_call", (data) => {
	frappe.show_alert({
		message: `📞 Unmatched call from: ${data.number}`,
		indicator: 'red'
	}, 10);
});
