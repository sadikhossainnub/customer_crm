import frappe
from frappe.model.document import Document
from frappe import _


class AgentCallTarget(Document):
	def validate(self):
		if self.from_date and self.to_date and self.from_date > self.to_date:
			frappe.throw(_("From Date cannot be after To Date"))
