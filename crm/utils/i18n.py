"""Shared i18n helpers for user-visible DocType labels."""

from __future__ import annotations

import frappe
from frappe import _


def get_session_language() -> str:
	"""Language for the current session (Guest uses System Settings)."""
	if frappe.session.user and frappe.session.user != "Guest":
		language = frappe.db.get_value("User", frappe.session.user, "language")
	else:
		language = frappe.db.get_single_value("System Settings", "language")
	# CRM deployment defaults to Simplified Chinese.
	return language or "zh"


def ensure_chinese_system_language() -> None:
	"""Keep System Settings aligned with CRM Chinese defaults after migrate."""
	if frappe.flags.in_install:
		return
	current = frappe.db.get_single_value("System Settings", "language")
	if not current:
		frappe.db.set_single_value("System Settings", "language", "zh")


def get_doctype_label(reference_doctype: str | None) -> str:
	"""Return a translated display label for a CRM DocType name."""
	if not reference_doctype:
		return ""
	key = reference_doctype.replace("CRM ", "")
	return _(key)


def apply_user_locale_defaults() -> None:
	"""Ensure logged-in users inherit Chinese system defaults when unset."""
	user_name = frappe.session.user
	if user_name in ("Guest", "Administrator"):
		return

	language = frappe.db.get_single_value("System Settings", "language") or "zh"
	time_zone = frappe.db.get_single_value("System Settings", "time_zone") or "Asia/Shanghai"

	updates: dict[str, str] = {}
	current_language = frappe.db.get_value("User", user_name, "language")
	current_time_zone = frappe.db.get_value("User", user_name, "time_zone")

	if not current_language:
		updates["language"] = language
	if not current_time_zone:
		updates["time_zone"] = time_zone

	if updates:
		frappe.db.set_value("User", user_name, updates, update_modified=False)
