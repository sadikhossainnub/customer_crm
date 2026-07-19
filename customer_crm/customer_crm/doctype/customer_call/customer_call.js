frappe.ui.form.on('Customer Call', {
	refresh: function(frm) {
		if (frm.is_new() && !frm.doc.next_follow_up_date) {
			frm.set_value('next_follow_up_date', get_next_working_day(7));
		}
		render_conversation_history(frm);
		fetch_last_call_detail(frm);

		// Click-to-Call via MicroSIP (sip: URI handler)
		if (frm.fields_dict.phone && frm.fields_dict.phone.grid) {
			frm.fields_dict.phone.grid.add_custom_button(__('📞 Call'), function() {
				let selected = frm.fields_dict.phone.grid.get_selected_children();
				if (selected.length) {
					let number = selected[0].phone;
					window.location.href = `sip:${number}`;
					frappe.show_alert({
						message: __('Dialing {0} via MicroSIP...', [number]),
						indicator: 'green'
					}, 5);
				} else {
					frappe.msgprint(__('Please select a phone number row first.'));
				}
			});
		}

		// Create Sales Order button (only for saved docs with a customer)
		if (!frm.is_new() && frm.doc.customer) {
			frm.add_custom_button(__('Sales Order'), function() {
				frappe.call({
					method: 'customer_crm.customer_crm.doctype.customer_call.customer_call.make_sales_order',
					args: {
						source_name: frm.doc.name
					},
					freeze: true,
					freeze_message: __('Creating Sales Order...'),
					callback: function(r) {
						if (r.message) {
							frappe.model.sync(r.message);
							frappe.set_route('Form', 'Sales Order', r.message.name);
						}
					}
				});
			}, __('Create'));
		}

		// Target vs Actual shortcut
		if (!frm.is_new()) {
			frm.add_custom_button(__('Target vs Actual'), function() {
				frappe.set_route('query-report/Call Target vs Actual', {
					agent: frm.doc.agent,
					from_date: frm.doc.call_date,
					to_date: frm.doc.call_date
				});
			}, __('Reports'));
		}

	},
	
	customer: function(frm) {
		render_conversation_history(frm);
		fetch_last_call_detail(frm);
		if (frm.doc.customer) {
			// Auto-fetch loyalty program, tier, and primary contact in one call
			frappe.db.get_value('Customer', frm.doc.customer, [
				'customer_primary_contact',
				'loyalty_program',
				'loyalty_program_tier'
			]).then(r => {
				if (r.message) {
					frm.set_value('contact_person', r.message.customer_primary_contact || '');
					frm.set_value('loyalty_program', r.message.loyalty_program || '');
					frm.set_value('tire', r.message.loyalty_program_tier || '');
				}
			});

			// Fetch all phone numbers
			frappe.call({
				method: 'customer_crm.customer_crm.api.call_api.get_customer_phones',
				args: {
					customer: frm.doc.customer
				},
				callback: function(r) {
					frm.clear_table('phone');
					if (r.message && r.message.length > 0) {
						r.message.forEach((p, index) => {
							let row = frm.add_child('phone');
							row.phone = p.phone;
							row.label = p.label;
							row.contact_person = p.contact_person;
							// Check the first one by default
							if (index === 0) {
								row.is_called = 1;
								if (p.contact_person) {
									frm.set_value('contact_person', p.contact_person);
								}
							} else {
								row.is_called = 0;
							}
						});
					}
					frm.refresh_field('phone');
				}
			});
		} else {
			frm.set_value('contact_person', '');
			frm.set_value('loyalty_program', '');
			frm.set_value('tire', '');
			frm.clear_table('phone');
			frm.refresh_field('phone');
		}
	},
	
	call_outcome: function(frm) {
		if (frm.doc.call_outcome) {
			frappe.db.get_value('Call Outcome', frm.doc.call_outcome, 'follow_up_days')
				.then(r => {
					let days = (r.message && r.message.follow_up_days !== undefined) ? r.message.follow_up_days : 7;
					frm.set_value('next_follow_up_date', get_next_working_day(days));
				});
		}
	}
});

frappe.ui.form.on('Customer Call Phone', {
	is_called: function(frm, cdt, cdn) {
		let row = frappe.get_doc(cdt, cdn);
		if (row.is_called) {
			// Uncheck all other phone rows
			frm.doc.phone.forEach(p => {
				if (p.name !== row.name && p.is_called) {
					frappe.model.set_value(p.doctype, p.name, 'is_called', 0);
				}
			});
			// Optionally update contact_person to the contact person for this number
			if (row.contact_person && row.contact_person !== frm.doc.customer) {
				frm.set_value('contact_person', row.contact_person);
			}
		}
	}
});

function get_next_working_day(days) {
	let date = frappe.datetime.add_days(frappe.datetime.get_today(), days);
	let day_of_week = moment(date).day();
	
	// If it's Saturday (6) or Sunday (0), move to next Monday
	if (day_of_week === 0) {
		date = frappe.datetime.add_days(date, 1);
	} else if (day_of_week === 6) {
		date = frappe.datetime.add_days(date, 2);
	}
	
	return date;
}

function render_conversation_history(frm) {
	if (!frm.doc.customer) {
		frm.set_df_property('conversation_history', 'options', '<div style="color: #888; padding: 15px;">Please select a Customer to view conversation history.</div>');
		return;
	}

	frappe.call({
		method: 'customer_crm.customer_crm.api.call_api.get_customer_history',
		args: {
			customer: frm.doc.customer,
			current_call: frm.doc.name
		},
		callback: function(r) {
			let html = '';
			if (r.message && r.message.length > 0) {
				html += '<div style="margin-top: 15px; max-height: 400px; overflow-y: auto; padding-right: 10px;">';
				r.message.forEach(call => {
					let date_str = frappe.datetime.global_date_format(call.call_date);
					let time_str = call.call_time ? call.call_time.substring(0, 5) : '';
					let outcome_class = 'bg-light text-muted';
					if (call.call_outcome === 'Interested') {
						outcome_class = 'badge-success';
					} else if (call.call_outcome === 'Callback Required') {
						outcome_class = 'badge-warning';
					} else if (call.call_outcome === 'Not Interested') {
						outcome_class = 'badge-danger';
					}

					html += `
						<div style="border-left: 2px solid var(--border-color, #e2e8f0); padding-left: 20px; position: relative; margin-bottom: 20px; font-size: 13px;">
							<div style="width: 12px; height: 12px; border-radius: 50%; background-color: var(--primary, #1b65b1); position: absolute; left: -7px; top: 4px; border: 2px solid var(--card-bg, #fff);"></div>
							
							<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
								<span style="font-weight: 600; color: var(--text-muted, #64748b);">
									${date_str} ${time_str} &nbsp;•&nbsp; Agent: ${call.agent_name}
								</span>
								${call.call_outcome ? `<span class="badge ${outcome_class}" style="font-size: 11px; padding: 3px 8px;">${call.call_outcome}</span>` : ''}
							</div>
							
							${call.conversation_summary ? `
								<div style="margin-bottom: 6px; color: var(--text-color, #1e293b);">
									<strong>Summary:</strong> ${call.conversation_summary}
								</div>
							` : ''}
						</div>
					`;
				});
				html += '</div>';
			} else {
				html = '<div style="color: var(--text-muted, #888); padding: 15px; font-style: italic;">No previous calls found for this customer.</div>';
			}
			frm.set_df_property('conversation_history', 'options', html);
		}
	});
}

function fetch_last_call_detail(frm) {
	if (frm.doc.customer) {
		frappe.call({
			method: 'customer_crm.customer_crm.api.call_api.get_last_call_detail',
			args: {
				customer: frm.doc.customer,
				current_call: frm.doc.name
			},
			callback: function(r) {
				if (r.message) {
					frm.set_value('last_call_detail', r.message);
				} else {
					frm.set_value('last_call_detail', 'No previous calls');
				}
			}
		});
	} else {
		frm.set_value('last_call_detail', 'No customer selected');
	}
}