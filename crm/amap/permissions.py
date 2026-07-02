# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe


def get_poi_sync_job_permission_query_conditions(user=None):
	if not user:
		user = frappe.session.user

	if user == "Administrator":
		return ""

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

	roles = frappe.get_roles(user)
	if "System Manager" in roles:
		return ""

	if "Sales Manager" in roles:
		from crm.permissions.org_hierarchy import hierarchy_enabled, _in_hierarchy

		if not hierarchy_enabled() or not _in_hierarchy(user):
			return ""

	return f"`tabCRM POI Record`.`job_owner` = {frappe.db.escape(user)}"


def has_poi_sync_job_permission(doc, ptype, user):
	return _has_owner_permission(doc, ptype, user, "job_owner")


def has_poi_record_permission(doc, ptype, user):
	return _has_owner_permission(doc, ptype, user, "job_owner")


def _has_owner_permission(doc, ptype, user, owner_field):
	if not user:
		user = frappe.session.user

	if user == "Administrator":
		return True

	roles = frappe.get_roles(user)
	if "System Manager" in roles:
		return True

	if "Sales Manager" in roles:
		from crm.permissions.org_hierarchy import hierarchy_enabled, _in_hierarchy

		if not hierarchy_enabled() or not _in_hierarchy(user):
			return True

	return doc.get(owner_field) == user
