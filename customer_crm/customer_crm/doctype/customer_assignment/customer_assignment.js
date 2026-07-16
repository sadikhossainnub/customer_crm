frappe.ui.form.on('Customer Assignment', {
	refresh: function(frm) {
		// Show assignment summary in form header
		if (!frm.is_new()) {
			const agentCount = (frm.doc.agents || []).length;
			const customerCount = (frm.doc.customers || []).length;
			frm.set_intro(
				`<b>${agentCount}</b> agent(s) assigned to 
				<b>${customerCount}</b> customer(s) from 
				<b>${frappe.datetime.str_to_user(frm.doc.from_date)}</b> to 
				<b>${frappe.datetime.str_to_user(frm.doc.to_date)}</b>.`,
				frm.doc.is_active ? 'blue' : 'yellow'
			);
		}

		// Highlight expired assignments
		if (frm.doc.to_date && frappe.datetime.str_to_obj(frm.doc.to_date) < new Date()) {
			frm.dashboard.add_comment(__('This assignment has expired.'), 'yellow', true);
		}
	},

	from_date: function(frm) {
		frm.trigger('validate_dates');
	},

	to_date: function(frm) {
		frm.trigger('validate_dates');
	},

	validate_dates: function(frm) {
		if (frm.doc.from_date && frm.doc.to_date) {
			if (frm.doc.from_date > frm.doc.to_date) {
				frappe.msgprint(__('Default From Date cannot be greater than Default To Date.'));
				frm.set_value('to_date', '');
			}
		}
	}
});

// Row defaults for agents
frappe.ui.form.on('Customer Assignment Agent', {
	agents_add: function(frm, cdt, cdn) {
		let row = frappe.get_doc(cdt, cdn);
		if (frm.doc.from_date && !row.from_date) {
			row.from_date = frm.doc.from_date;
		}
		if (frm.doc.to_date && !row.to_date) {
			row.to_date = frm.doc.to_date;
		}
		frm.refresh_field('agents');
	}
});

// Row defaults for customers
frappe.ui.form.on('Customer Assignment Customer', {
	customers_add: function(frm, cdt, cdn) {
		let row = frappe.get_doc(cdt, cdn);
		if (frm.doc.from_date && !row.from_date) {
			row.from_date = frm.doc.from_date;
		}
		if (frm.doc.to_date && !row.to_date) {
			row.to_date = frm.doc.to_date;
		}
		frm.refresh_field('customers');
	}
});
