frappe.ui.form.on('Customer', {
	refresh: function(frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(__('Customer Call'), function() {
				frappe.new_doc('Customer Call', {
					customer: frm.doc.name
				});
			}, __('Create'));

			frm.add_custom_button(__('View Call History'), function() {
				frappe.set_route('List', 'Customer Call', {
					customer: frm.doc.name
				});
			}, __('View'));
		}
	}
});