# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _

from crm.integrations.tripai.auth import handle_launch_ticket, is_tripai_enabled
from crm.integrations.tripai.settings import TripAIConfigError, get_tripai_settings


@frappe.whitelist(allow_guest=True)
def exchange_launch_ticket(ticket: str, project_key: str | None = None):
	"""Exchange TripAI launch ticket and establish Frappe session (SPA callback path)."""
	if not is_tripai_enabled():
		frappe.throw(_("TripAI integration is not enabled"), frappe.PermissionError)

	result = handle_launch_ticket(ticket, project_key)
	return {
		"success": True,
		"user": result["crm_user"],
		"role": result["crm_role"],
		"redirect_to": get_tripai_settings()["default_redirect_path"],
	}


@frappe.whitelist(allow_guest=True)
def get_integration_status():
	"""Return whether TripAI integration is enabled (no secrets)."""
	try:
		settings = get_tripai_settings()
	except TripAIConfigError:
		return {"enabled": False, "configured": False}

	return {
		"enabled": bool(settings["enabled"]),
		"configured": bool(settings["base_url"] and settings["runtime_token"]),
		"tool_key": settings["tool_key"],
		"project_key": settings["project_key"],
		"recharge_url": f"{settings['base_url']}/zh/dashboard",
	}


@frappe.whitelist(allow_guest=True)
def exchange_session(phone: str, password: str, device: str | None = None):
	"""Relay phone login via TripAI platform (direct CRM domain access).

	TripAI phone auth must not be called from the browser; this endpoint proxies
	the exchange on the server side once Phase 1 relay is wired.
	"""
	frappe.throw(_("Phone relay login is not implemented yet"), frappe.NotImplementedError)
