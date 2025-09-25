frappe.ui.form.on('Customer Call', {
	refresh: function(frm) {
		if (frm.is_new() && !frm.doc.next_follow_up_date) {
			frm.set_value('next_follow_up_date', get_next_working_day(7));
		}
	},
	
	customer: function(frm) {
		if (frm.doc.customer) {
			// Auto-fetch customer phone from contact
			frappe.db.get_value('Customer', frm.doc.customer, 'mobile_no')
				.then(r => {
					if (r.message && r.message.mobile_no) {
						frm.set_value('phone', r.message.mobile_no);
					}
				});
		}
	},
	
	call_outcome: function(frm) {
		// Auto-suggest next follow-up date based on outcome
		if (frm.doc.call_outcome === 'Callback Required') {
			frm.set_value('next_follow_up_date', get_next_working_day(1));
			frm.set_value('assigned_to', frappe.session.user);
		} else if (frm.doc.call_outcome === 'Interested') {
			frm.set_value('next_follow_up_date', get_next_working_day(3));
			frm.set_value('assigned_to', frappe.session.user);
		} else {
			frm.set_value('next_follow_up_date', get_next_working_day(7));
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