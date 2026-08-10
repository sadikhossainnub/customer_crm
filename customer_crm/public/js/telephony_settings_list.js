frappe.listview_settings['Telephony Settings'] = {
	onload: function(listview) {
		listview.page.add_inner_button(__('⬇️ Download MicroSIP Bridge App'), function() {
			window.open('/api/method/customer_crm.customer_crm.api.call_api.download_microsip_bridge');
		});
	}
};
