import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import getdate, nowdate


class AgentCallTarget(Document):
	def autoname(self):
		"""
		Custom naming: AgentName.DD.MM.YY.##
		Example: Sayed.17.07.26.01
		"""
		# Get agent short name (username before @, or first word of full name)
		agent_name = self._get_agent_short_name()

		# Format date as DD.MM.YY
		date = getdate(self.from_date or nowdate())
		dd = date.strftime("%d")
		mm = date.strftime("%m")
		yy = date.strftime("%y")

		# Build prefix: AgentName.DD.MM.YY.
		prefix = f"{agent_name}.{dd}.{mm}.{yy}."

		# Find next sequence number for this prefix
		seq = self._get_next_seq(prefix)

		self.name = f"{prefix}{seq:02d}"

	def _get_agent_short_name(self):
		"""Return a clean short name from the agent User."""
		if not self.agent:
			return "Unknown"

		# Try full_name first, take first word
		full_name = frappe.db.get_value("User", self.agent, "full_name") or ""
		if full_name:
			# First word of full name, strip spaces, keep alphanumeric only
			short = full_name.strip().split()[0]
			short = "".join(c for c in short if c.isalnum())
			if short:
				return short

		# Fallback: username part before @
		username = self.agent.split("@")[0]
		username = "".join(c for c in username if c.isalnum())
		return username or "Agent"

	def _get_next_seq(self, prefix):
		"""Find next sequential number for a given prefix."""
		existing = frappe.db.sql(
			"""SELECT name FROM `tabAgent Call Target`
				WHERE name LIKE %s
				ORDER BY name DESC LIMIT 1""",
			(frappe.db.escape(prefix) + "%",),
		)
		if not existing:
			return 1
		last_name = existing[0][0]  # e.g. "Sayed.17.07.26.03"
		try:
			last_seq = int(last_name.replace(prefix, ""))
			return last_seq + 1
		except (ValueError, TypeError):
			return 1

	def validate(self):
		if self.from_date and self.to_date and self.from_date > self.to_date:
			frappe.throw(_("From Date cannot be after To Date"))
