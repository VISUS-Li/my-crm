# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
import requests
from frappe import _

from crm.integrations.tripai.auth import handle_launch_ticket, is_tripai_enabled
from crm.integrations.tripai.license import activate_license_key as activate_tripai_license
from crm.integrations.tripai.license import get_user_entitlement, is_license_check_enabled
from crm.integrations.tripai.outbound import apply_ai_outbound_callback, request_ai_outbound_call
from crm.integrations.tripai.relay import TripAIRelayAuthError, handle_direct_login
from crm.integrations.tripai.settings import TripAIConfigError, get_tripai_settings


def _relay_login_response(result: dict) -> dict:
	return {
		"success": True,
		"user": result["crm_user"],
		"role": result["crm_role"],
		"redirect_to": result.get("redirect_to") or get_tripai_settings()["default_redirect_path"],
	}


def _perform_relay_login(login_id: str, password: str) -> dict:
	if not is_tripai_enabled():
		frappe.throw(_("TripAI integration is not enabled"), frappe.PermissionError)

	try:
		result = handle_direct_login(login_id, password)
	except TripAIRelayAuthError as exc:
		status = exc.status_code or 401
		if status == 503:
			frappe.throw(str(exc), title=_("TripAI Unreachable"), exc=frappe.ValidationError)
		if status in (400, 401, 403):
			frappe.throw(_("Invalid phone, email, or password"), frappe.AuthenticationError)
		frappe.throw(str(exc), frappe.ValidationError)

	return _relay_login_response(result)


@frappe.whitelist(allow_guest=True)
def login(login_id: str, password: str):
	"""Direct CRM login with TripAI phone or email + password (server relay)."""
	return _perform_relay_login(login_id, password)


@frappe.whitelist(allow_guest=True)
def exchange_launch_ticket(ticket: str, project_key: str | None = None):
	"""Exchange TripAI launch ticket and establish Frappe session (API / tests)."""
	if not is_tripai_enabled():
		frappe.throw(_("TripAI integration is not enabled"), frappe.PermissionError)

	result = handle_launch_ticket(ticket, project_key)
	return {
		"success": True,
		"user": result["crm_user"],
		"role": result["crm_role"],
		"redirect_to": get_tripai_settings()["default_redirect_path"],
	}


@frappe.whitelist()
def test_connection():
	"""Verify CRM server can reach the configured TripAI base URL."""
	frappe.only_for("System Manager")
	try:
		settings = get_tripai_settings()
	except TripAIConfigError as exc:
		return {"success": False, "message": str(exc)}

	base_url = settings["base_url"]
	try:
		response = requests.get(base_url, timeout=15, allow_redirects=False)
	except requests.RequestException as exc:
		return {
			"success": False,
			"message": f"Cannot reach TripAI at {base_url}. Ensure TripAI is running and CRM server can access it.",
			"detail": str(exc),
			"base_url": base_url,
		}

	status = response.status_code
	if status >= 500:
		return {
			"success": False,
			"message": f"TripAI responded with HTTP {status}",
			"base_url": base_url,
		}

	return {
		"success": True,
		"message": f"TripAI reachable at {base_url} (HTTP {status})",
		"base_url": base_url,
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
		"require_license": is_license_check_enabled(),
		"require_license_setting": bool(settings.get("require_license", False)),
		"phone_sales_mode": bool(
			frappe.db.get_single_value("FCRM Settings", "enable_phone_sales_mode")
			if frappe.db.exists("DocType", "FCRM Settings")
			else False
		),
		"recharge_url": f"{settings['base_url']}/zh/dashboard",
		"shop_url": f"{settings['base_url']}/zh/dashboard",
	}


@frappe.whitelist()
def get_license_status():
	"""Return current user's TripAI tool license entitlement."""
	return get_user_entitlement()


@frappe.whitelist()
def activate_license_key(license_key: str, device_id: str, device_label: str | None = None):
	"""Activate a TripAI license key for the current CRM user."""
	return activate_tripai_license(
		frappe.session.user,
		license_key,
		device_id,
		device_label=device_label,
	)


@frappe.whitelist()
def request_ai_outbound(lead_name: str, script: str | None = None):
	return request_ai_outbound_call(lead_name, script=script)


@frappe.whitelist()
def ai_outbound_callback(lead_name: str, score: int | None = None, summary: str | None = None, intent: str | None = None):
	return apply_ai_outbound_callback(lead_name, score=score, summary=summary, intent=intent)


@frappe.whitelist(allow_guest=True)
def exchange_session(phone: str, password: str, device: str | None = None):
	"""Alias for relay login (direct CRM domain access)."""
	_ = device
	return _perform_relay_login(phone, password)
