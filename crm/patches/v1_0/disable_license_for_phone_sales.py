"""Web SaaS (phone-sales mode): POI sync uses credits only, not license keys."""

import frappe


def execute():
	if not frappe.db.get_single_value("FCRM Settings", "enable_phone_sales_mode"):
		return

	if not frappe.db.exists("DocType", "CRM TripAI Settings"):
		return

	frappe.db.set_single_value("CRM TripAI Settings", "require_license", 0)
