# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.utils.caching import request_cache

_OWNER_FIELD = {
	"CRM Lead": "lead_owner",
	"CRM Deal": "deal_owner",
}


def hierarchy_enabled() -> bool:
	return bool(frappe.db.get_single_value("FCRM Settings", "enable_sales_hierarchy"))


def _permission_query_conditions(user: str | None, doctype: str):
	if not user:
		user = frappe.session.user

	if user == "Administrator":
		return ""

	from crm.permissions.agent_tenant import get_scoped_agent_tenant_id

	roles = frappe.get_roles(user)
	scoped_tenant = get_scoped_agent_tenant_id(user)

	if "System Manager" in roles and not scoped_tenant:
		return ""

	in_tree = hierarchy_enabled() and _in_hierarchy(user)

	# Sales Manager outside the tree retains the default ie sees everything
	if "Sales Manager" in roles and not in_tree and not scoped_tenant:
		return ""

	owner_field = _OWNER_FIELD[doctype]
	DT = frappe.qb.DocType(doctype)
	Todo = frappe.qb.DocType("ToDo").as_("_todo")

	tenant_filter = None
	if scoped_tenant and doctype == "CRM Lead":
		tenant_filter = DT.tripai_agent_tenant_id == scoped_tenant

	if in_tree:
		q1 = (DT[owner_field] == user) | DT[owner_field].isin(_team_mem_query(user))
		q2 = DT.name.isin(
			frappe.qb.from_(Todo)
			.select(Todo.reference_name)
			.where(
				(Todo.reference_type == doctype)
				& (Todo.status != "Cancelled")
				& ((Todo.allocated_to == user) | (Todo.allocated_to.isin(_team_mem_query(user))))
			)
		)
		base = q1 | q2
		if tenant_filter is not None:
			return base & tenant_filter
		return base

	q1 = DT[owner_field] == user
	q2 = DT.name.isin(
		frappe.qb.from_(Todo)
		.select(Todo.reference_name)
		.where((Todo.reference_type == doctype) & (Todo.status != "Cancelled") & (Todo.allocated_to == user))
	)
	base = q1 | q2

	if scoped_tenant and "Sales Manager" in roles and doctype == "CRM Lead":
		return DT.tripai_agent_tenant_id == scoped_tenant

	if tenant_filter is not None:
		return base & tenant_filter
	return base


def get_lead_permission_query_conditions(user=None):
	cond = _permission_query_conditions(user, "CRM Lead")
	return cond.get_sql(quote_char="`", secondary_quote_char="'") if cond else ""


def get_deal_permission_query_conditions(user=None):
	cond = _permission_query_conditions(user, "CRM Deal")
	return cond.get_sql(quote_char="`", secondary_quote_char="'") if cond else ""


def _has_permission(doc, ptype, user, doctype: str) -> bool | None:
	if not user:
		user = frappe.session.user

	if user == "Administrator":
		return True

	roles = frappe.get_roles(user)
	scoped_tenant = None
	try:
		from crm.permissions.agent_tenant import get_scoped_agent_tenant_id

		scoped_tenant = get_scoped_agent_tenant_id(user)
	except ImportError:
		pass

	if "System Manager" in roles and not scoped_tenant:
		return True

	if ptype == "create" or not doc.name:
		return True

	in_tree = hierarchy_enabled() and _in_hierarchy(user)
	if "Sales Manager" in roles and not in_tree and not scoped_tenant:
		return True

	if scoped_tenant and doc.get("tripai_agent_tenant_id") and doc.get("tripai_agent_tenant_id") != scoped_tenant:
		return False

	if scoped_tenant and "Sales Manager" in roles:
		return doc.get("tripai_agent_tenant_id") == scoped_tenant

	conditions = _permission_query_conditions(user, doctype)
	DT = frappe.qb.DocType(doctype)
	return bool(
		frappe.qb.from_(DT).select(DT.name).where(DT.name == doc.name).where(conditions).limit(1).run()
	)


def has_lead_permission(doc, ptype, user):
	return _has_permission(doc, ptype, user, "CRM Lead")


def has_deal_permission(doc, ptype, user):
	return _has_permission(doc, ptype, user, "CRM Deal")


def _in_hierarchy(user: str) -> bool:
	return bool(frappe.db.exists("CRM Sales Hierarchy", {"user": user}))


def _team_mem_query(user: str):
	Mgr = frappe.qb.DocType("CRM Sales Hierarchy").as_("_sqmgr")
	Member = frappe.qb.DocType("CRM Sales Hierarchy").as_("_sqmem")
	return (
		frappe.qb.from_(Mgr)
		.join(Member)
		.on((Member.lft >= Mgr.lft) & (Member.lft <= Mgr.rgt))
		.select(Member.user)
		.where(Mgr.user == user)
	)
