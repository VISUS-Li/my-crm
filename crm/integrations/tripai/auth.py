# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import now_datetime

from crm.integrations.tripai.client import TripAIAPIError, exchange_launch_ticket
from crm.integrations.tripai.settings import TripAIConfigError, get_tripai_settings
from crm.integrations.tripai.user_contact import (
	build_user_link_contact_fields,
	normalize_tripai_user_id,
	resolve_primary_contact,
)

CRM_ROLE_SYSTEM_MANAGER = "System Manager"
CRM_ROLE_SALES_MANAGER = "Sales Manager"
CRM_ROLE_SALES_USER = "Sales User"


def is_tripai_enabled() -> bool:
	try:
		return bool(get_tripai_settings()["enabled"])
	except TripAIConfigError:
		return False


def map_tripai_user_to_crm_role(tripai_user: dict[str, Any]) -> str:
	if tripai_user.get("role") == "admin":
		return CRM_ROLE_SYSTEM_MANAGER

	agent_tenant = tripai_user.get("agentTenant") or {}
	if agent_tenant.get("status") == "active" and agent_tenant.get("level") == 1:
		return CRM_ROLE_SALES_MANAGER

	return CRM_ROLE_SALES_USER


def normalize_tripai_email(tripai_user: dict[str, Any]) -> str:
	return normalize_tripai_user_id(tripai_user)


def ensure_crm_user(tripai_user: dict[str, Any], crm_role: str) -> str:
	email = normalize_tripai_user_id(tripai_user)
	primary = resolve_primary_contact(tripai_user)
	display_name = (tripai_user.get("name") or primary["display"] or email.split("@")[0]).strip() or email
	phone = primary.get("tripai_phone")

	if frappe.db.exists("User", email):
		user = frappe.get_doc("User", email)
	else:
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": display_name[:140],
				"send_welcome_email": 0,
				"user_type": "System User",
				"enabled": 1,
			}
		)
		user.insert(ignore_permissions=True)

	if phone:
		user.mobile_no = phone
	if display_name:
		user.first_name = display_name[:140]

	desired_roles = {crm_role}
	if crm_role == CRM_ROLE_SYSTEM_MANAGER:
		desired_roles.update({CRM_ROLE_SALES_MANAGER, CRM_ROLE_SALES_USER})
	elif crm_role == CRM_ROLE_SALES_MANAGER:
		desired_roles.add(CRM_ROLE_SALES_USER)

	current_roles = set(frappe.get_roles(user.name))
	for role in desired_roles - current_roles:
		user.add_roles(role)

	if crm_role == CRM_ROLE_SALES_USER:
		_update_sales_user_modules(user)

	user.save(ignore_permissions=True)
	return user.name


def _update_sales_user_modules(user) -> None:
	block_modules = frappe.get_all(
		"Module Def",
		fields=["name as module"],
		filters={"name": ["!=", "FCRM"]},
	)
	if block_modules:
		user.set("block_modules", block_modules)


def upsert_user_link(tripai_user: dict[str, Any], crm_user: str, crm_role: str) -> str:
	tripai_user_id = tripai_user["id"]
	agent_tenant = tripai_user.get("agentTenant") or {}

	existing = frappe.db.get_value(
		"CRM TripAI User Link",
		{"tripai_user_id": tripai_user_id},
		"name",
	)

	values = {
		"tripai_user_id": tripai_user_id,
		"crm_user": crm_user,
		"tripai_role": tripai_user.get("role"),
		"agent_tenant_id": agent_tenant.get("id"),
		"agent_tenant_level": agent_tenant.get("level"),
		"last_login_at": now_datetime(),
		"enabled": 1,
		**build_user_link_contact_fields(tripai_user),
	}

	if existing:
		doc = frappe.get_doc("CRM TripAI User Link", existing)
		doc.update(values)
		doc.save(ignore_permissions=True)
		return doc.name

	doc = frappe.get_doc({"doctype": "CRM TripAI User Link", **values})
	doc.insert(ignore_permissions=True)
	return doc.name


def login_crm_user(crm_user: str) -> None:
	frappe.local.login_manager.login_as(crm_user)
	frappe.db.commit()


def handle_launch_ticket(ticket: str, project_key: str | None = None) -> dict[str, Any]:
	if not ticket:
		frappe.throw(_("Missing launch ticket"), frappe.ValidationError)

	try:
		exchanged = exchange_launch_ticket(ticket, project_key)
	except TripAIAPIError as exc:
		if exc.status_code in (400, 403):
			frappe.throw(_("Invalid or expired launch ticket"), frappe.AuthenticationError)
		frappe.throw(_("TripAI authentication failed: {0}").format(str(exc)))

	tripai_user = exchanged.get("user") or {}
	if not tripai_user.get("id"):
		frappe.throw(_("TripAI user payload is incomplete"), frappe.AuthenticationError)

	crm_role = map_tripai_user_to_crm_role(tripai_user)
	crm_user = ensure_crm_user(tripai_user, crm_role)
	link_name = upsert_user_link(tripai_user, crm_user, crm_role)
	login_crm_user(crm_user)

	return {
		"crm_user": crm_user,
		"crm_role": crm_role,
		"tripai_user_id": tripai_user["id"],
		"user_link": link_name,
	}


def get_redirect_path() -> str:
	try:
		return get_tripai_settings()["default_redirect_path"] or "/crm"
	except TripAIConfigError:
		return "/crm"
