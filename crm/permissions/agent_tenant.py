# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors

from __future__ import annotations

import frappe


def resolve_agent_tenant_id(crm_user: str | None = None) -> str | None:
	crm_user = crm_user or frappe.session.user
	if not crm_user or crm_user == "Guest":
		return None

	link_tenant = frappe.db.get_value(
		"CRM TripAI User Link",
		{"crm_user": crm_user, "enabled": 1},
		"agent_tenant_id",
	)
	if link_tenant:
		return link_tenant

	return frappe.db.get_value("User", crm_user, "tripai_agent_tenant_id")


def inherit_agent_tenant_from_inviter(invitee_email: str, inviter: str) -> None:
	tenant_id = resolve_agent_tenant_id(inviter)
	if not tenant_id or not frappe.db.exists("User", invitee_email):
		return
	frappe.db.set_value("User", invitee_email, "tripai_agent_tenant_id", tenant_id)


def user_has_agent_tenant(user: str | None = None) -> bool:
	return bool(resolve_agent_tenant_id(user))


def _is_platform_admin(user: str) -> bool:
	if user == "Administrator":
		return True
	if "System Manager" not in frappe.get_roles(user):
		return False
	return frappe.db.get_value(
		"CRM TripAI User Link",
		{"crm_user": user, "enabled": 1},
		"tripai_role",
	) == "admin"


def get_scoped_agent_tenant_id(user: str | None = None) -> str | None:
	"""Return tenant id when user should be scoped to an agent; None = unrestricted."""
	user = user or frappe.session.user
	if _is_platform_admin(user):
		return None
	return resolve_agent_tenant_id(user)


def agent_tenant_condition(doctype: str, user: str | None = None) -> str | None:
	tenant_id = get_scoped_agent_tenant_id(user)
	if not tenant_id:
		return None
	return f"`tab{doctype}`.`agent_tenant_id` = {frappe.db.escape(tenant_id)}"


def lead_agent_tenant_condition(user: str | None = None) -> str | None:
	tenant_id = get_scoped_agent_tenant_id(user)
	if not tenant_id:
		return None
	return f"`tabCRM Lead`.`tripai_agent_tenant_id` = {frappe.db.escape(tenant_id)}"


def agent_tenant_matches(doc_tenant: str | None, user: str | None = None) -> bool:
	tenant_id = get_scoped_agent_tenant_id(user)
	if not tenant_id:
		return True
	return (doc_tenant or "") == tenant_id
