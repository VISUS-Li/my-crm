import json

import frappe

from crm.fcrm.doctype.crm_view_settings.crm_view_settings import normalize_list_columns


def execute():
	_ensure_phone_sales_mode_setting()
	_ensure_phone_sales_views()


def _ensure_phone_sales_mode_setting():
	if not frappe.db.exists("DocType", "FCRM Settings"):
		return

	if not frappe.db.exists(
		"Custom Field",
		{"dt": "FCRM Settings", "fieldname": "enable_phone_sales_mode"},
	):
		frappe.get_doc(
			{
				"doctype": "Custom Field",
				"dt": "FCRM Settings",
				"fieldname": "enable_phone_sales_mode",
				"label": "Enable Phone Sales Mode",
				"fieldtype": "Check",
				"default": "1",
				"insert_after": "enable_sales_hierarchy",
				"description": "Simplify CRM UI for Amap POI merchant outreach and phone follow-up",
			}
		).insert(ignore_permissions=True)

	frappe.db.set_single_value("FCRM Settings", "enable_phone_sales_mode", 1)


def _ensure_phone_sales_views():
	views = [
		{
			"label": "高德-待拨打",
			"icon": "phone",
			"dt": "CRM Lead",
			"type": "list",
			"route_name": "Leads",
			"pinned": 1,
			"is_default": 1,
			"filters": json.dumps(
				[
					["CRM Lead", "source", "like", "%高德%"],
					["CRM Lead", "has_valid_phone", "=", 1],
					["CRM Lead", "status", "=", "待拨打"],
				]
			),
			"order_by": "modified desc",
			"fieldnames": [
				"lead_name",
				"mobile_no",
				"organization",
				"recommended_product",
				"district",
				"status",
				"lead_owner",
			],
		},
		{
			"label": "高德-有意向",
			"icon": "star",
			"dt": "CRM Lead",
			"type": "list",
			"route_name": "Leads",
			"pinned": 1,
			"filters": json.dumps(
				[
					["CRM Lead", "source", "like", "%高德%"],
					["CRM Lead", "status", "in", ["有意向", "演示/试用", "报价"]],
				]
			),
			"order_by": "modified desc",
			"fieldnames": [
				"lead_name",
				"mobile_no",
				"organization",
				"recommended_product",
				"status",
				"lead_owner",
			],
		},
		{
			"label": "高德-今日已联系",
			"icon": "check",
			"dt": "CRM Lead",
			"type": "list",
			"route_name": "Leads",
			"pinned": 1,
			"filters": json.dumps(
				[
					["CRM Lead", "source", "like", "%高德%"],
					["CRM Lead", "status", "=", "已联系"],
				]
			),
			"order_by": "modified desc",
			"fieldnames": [
				"lead_name",
				"mobile_no",
				"organization",
				"recommended_product",
				"district",
				"lead_owner",
			],
		},
	]

	for view in views:
		fieldnames = view.pop("fieldnames")
		view["columns"] = json.dumps(normalize_list_columns(fieldnames, view["dt"]))
		existing = frappe.db.exists(
			"CRM View Settings", {"label": view["label"], "dt": view["dt"]}
		)
		if existing:
			frappe.db.set_value("CRM View Settings", existing, view, update_modified=False)
			continue

		frappe.get_doc(
			{
				"doctype": "CRM View Settings",
				"user": "",
				"public": 1,
				"is_standard": 1,
				**view,
			}
		).insert(ignore_permissions=True)
