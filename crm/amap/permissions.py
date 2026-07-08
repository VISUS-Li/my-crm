# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe


def get_poi_sync_job_permission_query_conditions(user=None):
	if not user:
		user = frappe.session.user

	if user == "Administrator":
		return ""

	from crm.permissions.agent_tenant import agent_tenant_condition, get_scoped_agent_tenant_id

	tenant_cond = agent_tenant_condition("CRM POI Sync Job", user)
	if tenant_cond:
		roles = frappe.get_roles(user)
		if "Sales User" in roles and "Sales Manager" not in roles:
			owner_cond = f"`tabCRM POI Sync Job`.`job_owner` = {frappe.db.escape(user)}"
			return f"({tenant_cond}) AND ({owner_cond})"
		return tenant_cond

	roles = frappe.get_roles(user)
	if "System Manager" in roles:
		return ""

	if "Sales Manager" in roles:
		from crm.permissions.org_hierarchy import hierarchy_enabled, _in_hierarchy

		if not hierarchy_enabled() or not _in_hierarchy(user):
			return ""

	return f"`tabCRM POI Sync Job`.`job_owner` = {frappe.db.escape(user)}"


def get_poi_record_permission_query_conditions(user=None):
	if not user:
		user = frappe.session.user

	if user == "Administrator":
		return ""

	from crm.permissions.agent_tenant import agent_tenant_condition

	tenant_cond = agent_tenant_condition("CRM POI Record", user)
	if tenant_cond:
		roles = frappe.get_roles(user)
		if "Sales User" in roles and "Sales Manager" not in roles:
			owner_cond = f"`tabCRM POI Record`.`job_owner` = {frappe.db.escape(user)}"
			return f"({tenant_cond}) AND ({owner_cond})"
		return tenant_cond

	roles = frappe.get_roles(user)
	if "System Manager" in roles:
		return ""

	if "Sales Manager" in roles:
		from crm.permissions.org_hierarchy import hierarchy_enabled, _in_hierarchy

		if not hierarchy_enabled() or not _in_hierarchy(user):
			return ""

	return f"`tabCRM POI Record`.`job_owner` = {frappe.db.escape(user)}"


def has_poi_sync_job_permission(doc, ptype, user):
	return _has_owner_permission(doc, ptype, user, "job_owner", "agent_tenant_id")


def has_poi_record_permission(doc, ptype, user):
	return _has_owner_permission(doc, ptype, user, "job_owner", "agent_tenant_id")


def _has_owner_permission(doc, ptype, user, owner_field, tenant_field):
	if not user:
		user = frappe.session.user

	if user == "Administrator":
		return True

	# job_owner / agent_tenant_id are set in validate(), which runs after create permission.
	if ptype == "create" or not getattr(doc, "name", None):
		return True

	from crm.permissions.agent_tenant import agent_tenant_matches, get_scoped_agent_tenant_id

	scoped_tenant = get_scoped_agent_tenant_id(user)
	if scoped_tenant and not agent_tenant_matches(doc.get(tenant_field), user):
		return False

	roles = frappe.get_roles(user)
	if "System Manager" in roles and not scoped_tenant:
		return True

	if "Sales Manager" in roles:
		if scoped_tenant:
			return True
		from crm.permissions.org_hierarchy import hierarchy_enabled, _in_hierarchy

		if not hierarchy_enabled() or not _in_hierarchy(user):
			return True

	return doc.get(owner_field) == user
