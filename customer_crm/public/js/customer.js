frappe.ui.form.on('Customer', {
	refresh: function(frm) {
		if (!frm.is_new()) {
			// ── Existing buttons ──────────────────────────────────
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

			// ── Assignment buttons ────────────────────────────────
			frm.add_custom_button(__('Assign to Agent'), function() {
				_show_assign_dialog(frm);
			}, __('Assignment'));

			frm.add_custom_button(__('View Assignments'), function() {
				frappe.set_route('List', 'Customer Assignment', {
					'customers.customer': frm.doc.name
				});
			}, __('Assignment'));

			// ── Show current assignment banner ────────────────────
			_load_assignment_status(frm);
		}
	}
});

/**
 * Query today's assignment for this customer and show a coloured banner.
 */
function _load_assignment_status(frm) {
	frappe.call({
		method: 'customer_crm.customer_crm.api.call_api.get_customer_assignment',
		args: { customer: frm.doc.name },
		callback: function(r) {
			if (r.message && r.message.length > 0) {
				const agents_info = r.message.map(a => {
					const from = frappe.datetime.str_to_user(a.agent_from);
					const to   = frappe.datetime.str_to_user(a.agent_to);
					return `<b>${a.agent_name || a.agent}</b> (${from} → ${to})`;
				}).join(', ');
				
				frm.dashboard.add_comment(
					`<i class="fa fa-user-circle"></i> &nbsp;
					<b>Assigned Agents:</b> ${agents_info}`,
					'blue',
					true
				);
			}
		}
	});
}

/**
 * Dialog to quickly assign this customer to an agent.
 */
function _show_assign_dialog(frm) {
	const d = new frappe.ui.Dialog({
		title: __('Assign Customer to Agent'),
		fields: [
			{
				fieldname: 'agent',
				fieldtype: 'Link',
				label: __('Agent'),
				options: 'User',
				reqd: 1,
				filters: { ignore_user_type: 1 }
			},
			{
				fieldname: 'col_break',
				fieldtype: 'Column Break'
			},
			{
				fieldname: 'from_date',
				fieldtype: 'Date',
				label: __('From Date'),
				reqd: 1,
				default: frappe.datetime.get_today()
			},
			{
				fieldname: 'to_date',
				fieldtype: 'Date',
				label: __('To Date'),
				reqd: 1
			},
			{
				fieldname: 'notes',
				fieldtype: 'Small Text',
				label: __('Notes')
			}
		],
		primary_action_label: __('Assign'),
		primary_action: function(values) {
			if (values.from_date > values.to_date) {
				frappe.msgprint(__('From Date cannot be greater than To Date.'));
				return;
			}
			frappe.call({
				method: 'customer_crm.customer_crm.api.call_api.quick_assign_customer',
				args: {
					customer: frm.doc.name,
					agent: values.agent,
					from_date: values.from_date,
					to_date: values.to_date,
					notes: values.notes || ''
				},
				freeze: true,
				freeze_message: __('Creating assignment…'),
				callback: function(r) {
					if (!r.exc) {
						d.hide();
						frappe.show_alert({
							message: __(`Customer assigned successfully! Record: ${r.message}`),
							indicator: 'green'
						});
						// Reload banner
						_load_assignment_status(frm);
					}
				}
			});
		}
	});
	d.show();
}