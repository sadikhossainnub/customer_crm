# Copyright (c) 2026, primetechbd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, today


class CustomerAssignment(Document):

    def validate(self):
        self._validate_header_dates()
        self._fill_default_dates()
        self._validate_row_dates()
        self._validate_no_duplicate_agents()
        self._validate_no_duplicate_customers()
        self._validate_customer_conflicts()

    # ─── Date helpers ─────────────────────────────────────────────────────────

    def _validate_header_dates(self):
        """Header from_date must not exceed to_date."""
        if self.from_date and self.to_date:
            if getdate(self.from_date) > getdate(self.to_date):
                frappe.throw("Default From Date cannot be greater than Default To Date.")

    def _fill_default_dates(self):
        """
        If a row's from_date / to_date is empty, inherit from the header.
        This makes adding a new row quick — just pick the agent/customer.
        """
        for row in self.agents:
            if not row.from_date:
                row.from_date = self.from_date
            if not row.to_date:
                row.to_date = self.to_date

        for row in self.customers:
            if not row.from_date:
                row.from_date = self.from_date
            if not row.to_date:
                row.to_date = self.to_date

    def _validate_row_dates(self):
        """Every row's from_date must not exceed its to_date."""
        for i, row in enumerate(self.agents, start=1):
            if row.from_date and row.to_date:
                if getdate(row.from_date) > getdate(row.to_date):
                    frappe.throw(
                        f"Agents row {i} ({row.agent}): From Date cannot exceed To Date."
                    )

        for i, row in enumerate(self.customers, start=1):
            if row.from_date and row.to_date:
                if getdate(row.from_date) > getdate(row.to_date):
                    frappe.throw(
                        f"Customers row {i} ({row.customer}): From Date cannot exceed To Date."
                    )

    # ─── Duplicate guards ─────────────────────────────────────────────────────

    def _validate_no_duplicate_agents(self):
        """Same agent must not appear more than once in the agents table."""
        seen = set()
        for row in self.agents:
            if row.agent in seen:
                frappe.throw(
                    f"Agent <b>{row.agent}</b> is listed more than once in the Agents table."
                )
            seen.add(row.agent)

    def _validate_no_duplicate_customers(self):
        """Same customer must not appear more than once in the customers table."""
        seen = set()
        for row in self.customers:
            if row.customer in seen:
                frappe.throw(
                    f"Customer <b>{row.customer}</b> is listed more than once "
                    f"in the Customers table."
                )
            seen.add(row.customer)

    # ─── Overlap conflict ─────────────────────────────────────────────────────

    def _validate_customer_conflicts(self):
        """
        A customer row must not overlap (by date) with a row for the *same customer*
        in another active Customer Assignment record that shares at least one agent.
        This prevents the same customer being handled by the same agent simultaneously
        in two separate assignment records.
        """
        my_agents = {row.agent for row in self.agents}
        if not my_agents:
            return

        for row in self.customers:
            conflicts = frappe.db.sql("""
                SELECT
                    ca.name,
                    caa.agent,
                    cac.from_date,
                    cac.to_date
                FROM `tabCustomer Assignment` ca
                JOIN `tabCustomer Assignment Agent`    caa ON caa.parent = ca.name
                JOIN `tabCustomer Assignment Customer` cac ON cac.parent = ca.name
                WHERE cac.customer  = %(customer)s
                  AND caa.agent     IN %(agents)s
                  AND ca.name      != %(self_name)s
                  AND ca.is_active  = 1
                  AND cac.from_date <= %(to_date)s
                  AND cac.to_date   >= %(from_date)s
            """, {
                "customer":  row.customer,
                "agents":    list(my_agents),
                "self_name": self.name or "__new__",
                "from_date": row.from_date or self.from_date,
                "to_date":   row.to_date   or self.to_date,
            }, as_dict=True)

            if conflicts:
                c = conflicts[0]
                frappe.throw(
                    f"Customer <b>{row.customer}</b> is already assigned to agent "
                    f"<b>{c.agent}</b> in record <b>{c.name}</b> "
                    f"({c.from_date} → {c.to_date}). Date ranges must not overlap."
                )
