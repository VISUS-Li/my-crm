"""Chinese locale defaults for new CRM installations."""

from __future__ import annotations

import frappe

CHINESE_DEFAULTS = {
	"language": "zh",
	"country": "China",
	"time_zone": "Asia/Shanghai",
	"currency": "CNY",
}


def apply_chinese_defaults() -> None:
	"""Apply Chinese language, timezone, country, and currency defaults."""
	for field, value in CHINESE_DEFAULTS.items():
		frappe.db.set_single_value("System Settings", field, value)

	if frappe.db.exists("DocType", "FCRM Settings"):
		current_currency = frappe.db.get_single_value("FCRM Settings", "currency")
		if not current_currency or current_currency == "USD":
			frappe.db.set_single_value("FCRM Settings", "currency", "CNY")

	frappe.db.set_value("User", "Administrator", "language", CHINESE_DEFAULTS["language"])
	frappe.db.set_value("User", "Administrator", "time_zone", CHINESE_DEFAULTS["time_zone"])
