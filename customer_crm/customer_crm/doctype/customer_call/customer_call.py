import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils import get_url


@frappe.whitelist()
def make_sales_order(source_name, target_doc=None):
	"""Create a new Sales Order pre-filled from a Customer Call record."""
	def set_missing_values(source, target):
		target.run_method("set_missing_values")
		target.run_method("set_other_charges")
		target.run_method("calculate_taxes_and_totals")

	doc = get_mapped_doc(
		"Customer Call",
		source_name,
		{
			"Customer Call": {
				"doctype": "Sales Order",
				"field_map": {
					"customer": "customer",
					"customer_name": "customer_name",
					"territory": "territory",
					"name": "customer_crm_call_id",
				},
				"validation": {
					"docstatus": ["!=", 2]
				}
			}
		},
		target_doc,
		set_missing_values,
	)
	return doc

class CustomerCall(Document):
	def validate(self):
		self.set_next_follow_up_date()

	def set_next_follow_up_date(self):
		if not self.next_follow_up_date and self.call_outcome:
			follow_up_days = frappe.db.get_value("Call Outcome", self.call_outcome, "follow_up_days")
			if follow_up_days is None:
				follow_up_days = 7
			
			from frappe.utils import add_days, getdate, today
			base_date = self.call_date or today()
			date = getdate(add_days(base_date, int(follow_up_days)))
			day_of_week = date.weekday()
			if day_of_week == 6:  # Sunday
				date = add_days(date, 1)
			elif day_of_week == 5:  # Saturday
				date = add_days(date, 2)
			
			self.next_follow_up_date = date

	def after_insert(self):
		"""Create follow-up task if next follow-up date is set"""
		if self.next_follow_up_date and self.agent:
			self.create_follow_up_task()
			self.send_notification()
	
	def create_follow_up_task(self):
		"""Create a follow-up task"""
		task = frappe.get_doc({
			"doctype": "ToDo",
			"description": f"Follow-up call for {self.customer}",
			"reference_type": "Customer Call",
			"reference_name": self.name,
			"assigned_by": frappe.session.user,
			"owner": self.agent,
			"date": self.next_follow_up_date,
			"priority": "Medium"
		})
		task.insert(ignore_permissions=True)
	
	def send_notification(self):
		"""Send notification to assigned user"""
		if not self.agent:
			return
			
		called_phone = 'Not available'
		if self.phone:
			for p in self.phone:
				if p.is_called:
					called_phone = p.phone
					break

		# Email notification
		frappe.sendmail(
			recipients=[self.agent],
			subject=f"Follow-up assigned: {self.customer}",
			message=f"""You have been assigned a follow-up call for {self.customer} on {self.next_follow_up_date}.
			
Call Details:
			- Customer: {self.customer}
			- Phone: {called_phone}
			- Follow-up Date: {self.next_follow_up_date}
			
View Call: {get_url()}/app/customer-call/{self.name}"""
		)
		
		# In-app notification
		frappe.publish_realtime(
			event="follow_up_assigned",
			message={
				"customer": self.customer,
				"date": self.next_follow_up_date,
				"call_id": self.name
			},
			user=self.agent
		)