import frappe
from frappe.model.document import Document
from frappe.utils import get_url

class CustomerCall(Document):
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