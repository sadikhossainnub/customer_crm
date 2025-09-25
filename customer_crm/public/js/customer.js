frappe.ui.form.on('Customer', {
	refresh: function(frm) {
		frm.add_custom_button(__('Follow-up'), function() {
			frappe.new_doc('Customer Call', {
				customer: frm.doc.name,
				phone: frm.doc.mobile_no
			});
		}, __('Actions'));
	}
});