# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors

from __future__ import annotations

import frappe


@frappe.whitelist()
def apply_connection_settings(
	base_url: str | None = None,
	enabled: int | None = None,
	project_key: str | None = None,
	tool_key: str | None = None,
):
	"""Apply TripAI connection settings (System Manager / bench execute)."""
	frappe.only_for("System Manager")
	doc = frappe.get_single("CRM TripAI Settings")

	if base_url:
		doc.base_url = base_url.strip().rstrip("/")
	if enabled is not None:
		doc.enabled = int(enabled)
	if project_key:
		doc.project_key = project_key.strip()
	if tool_key:
		doc.tool_key = tool_key.strip()

	doc.save(ignore_permissions=True)
	frappe.db.commit()

	return {
		"success": True,
		"enabled": bool(doc.enabled),
		"base_url": doc.base_url,
		"project_key": doc.project_key,
		"tool_key": doc.tool_key,
	}
