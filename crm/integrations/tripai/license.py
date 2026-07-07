# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from crm.integrations.tripai.billing import resolve_billing_tripai_user_id, resolve_tripai_user_id
from crm.integrations.tripai.client import (
	TripAIAPIError,
	TripAIConfigError,
	activate_delegated_license,
	fetch_delegated_entitlement,
)
from crm.integrations.tripai.settings import get_tripai_settings


class LicenseNotEntitledError(Exception):
	def __init__(self, message: str | None = None):
		self.message = message or _("TripAI license required for POI sync")
		super().__init__(self.message)


def _is_phone_sales_mode() -> bool:
	if not frappe.db.exists("DocType", "FCRM Settings"):
		return False
	return bool(frappe.db.get_single_value("FCRM Settings", "enable_phone_sales_mode"))


def is_license_check_enabled() -> bool:
	"""Whether POI sync must verify a TripAI tool license before billing."""
	if _is_phone_sales_mode():
		return False

	try:
		settings = get_tripai_settings()
	except TripAIConfigError:
		return False
	if not settings["enabled"] or not settings["runtime_token"]:
		return False
	return bool(settings.get("require_license", False))


def should_skip_license_check(crm_user: str | None = None) -> bool:
	if not is_license_check_enabled():
		return True

	crm_user = crm_user or frappe.session.user
	if not crm_user or crm_user == "Guest":
		return True

	if "System Manager" in frappe.get_roles(crm_user):
		link = frappe.db.get_value(
			"CRM TripAI User Link",
			{"crm_user": crm_user, "enabled": 1},
			["tripai_role"],
			as_dict=True,
		)
		if link and link.get("tripai_role") == "admin":
			return True

	return False


def get_user_entitlement(crm_user: str | None = None) -> dict[str, Any]:
	if not is_license_check_enabled():
		return {
			"entitled": True,
			"required": False,
			"skipped": True,
			"reason": "disabled",
		}

	crm_user = crm_user or frappe.session.user
	tripai_user_id = resolve_billing_tripai_user_id(crm_user)
	if not tripai_user_id:
		return {
			"entitled": False,
			"required": is_license_check_enabled(),
			"skipped": False,
			"reason": "not_linked",
		}

	if should_skip_license_check(crm_user):
		return {
			"entitled": True,
			"required": is_license_check_enabled(),
			"skipped": True,
			"reason": "exempt",
		}

	try:
		payload = fetch_delegated_entitlement(tripai_user_id)
	except TripAIAPIError as exc:
		frappe.log_error(title="TripAI entitlement check failed", message=str(exc))
		return {
			"entitled": False,
			"required": is_license_check_enabled(),
			"skipped": False,
			"reason": "api_error",
			"error": str(exc),
		}

	return {
		"entitled": bool(payload.get("entitled")),
		"required": is_license_check_enabled(),
		"skipped": False,
		"summary": payload.get("summary"),
		"keys": payload.get("keys"),
	}


def ensure_user_licensed(crm_user: str | None = None) -> None:
	if should_skip_license_check(crm_user):
		return

	entitlement = get_user_entitlement(crm_user)
	if entitlement.get("entitled"):
		return

	try:
		settings = get_tripai_settings()
		shop_url = f"{settings['base_url']}/zh/dashboard"
	except TripAIConfigError:
		shop_url = ""

	raise LicenseNotEntitledError(
		_(
			"Active TripAI license required for POI sync. Activate a license key on this sync job page, or purchase one at {0}"
		).format(shop_url or _("TripAI dashboard"))
	)


def activate_license_key(
	crm_user: str,
	license_key: str,
	device_id: str,
	device_label: str | None = None,
) -> dict[str, Any]:
	tripai_user_id = resolve_tripai_user_id(crm_user)
	if not tripai_user_id:
		frappe.throw(
			_("TripAI account is not linked. Please log in via the TripAI platform first."),
			title=_("TripAI Not Linked"),
		)

	try:
		return activate_delegated_license(
			tripai_user_id,
			license_key.strip(),
			device_id.strip(),
			device_label=device_label,
		)
	except TripAIAPIError as exc:
		message = str(exc)
		payload = exc.payload or {}
		if payload.get("message"):
			message = payload["message"]
		frappe.throw(message, title=_("License Activation Failed"))
