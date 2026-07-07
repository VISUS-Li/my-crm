"""APIs for phone-sales / merchant outreach workflow."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import getdate, nowdate


def _amap_lead_filters() -> list:
	return [
		["CRM Lead", "converted", "=", 0],
		["CRM Lead", "source", "like", "%高德%"],
	]


@frappe.whitelist()
def get_workbench_stats():
	"""Summary counts for the phone-sales workbench dashboard."""
	amap_filters = _amap_lead_filters()
	today = getdate(nowdate())

	pending_call = frappe.db.count(
		"CRM Lead",
		filters=amap_filters
		+ [
			["CRM Lead", "status", "=", "待拨打"],
			["CRM Lead", "has_valid_phone", "=", 1],
		],
	)

	interested = frappe.db.count(
		"CRM Lead",
		filters=amap_filters + [["CRM Lead", "status", "=", "有意向"]],
	)

	new_leads = frappe.db.count(
		"CRM Lead",
		filters=amap_filters + [["CRM Lead", "status", "=", "新线索"]],
	)

	contacted_today = frappe.db.count(
		"CRM Lead",
		filters=amap_filters
		+ [
			["CRM Lead", "status", "=", "已联系"],
			["CRM Lead", "modified", "between", [today, today]],
		],
	)

	invalid = frappe.db.count(
		"CRM Lead",
		filters=amap_filters + [["CRM Lead", "status", "=", "无效"]],
	)

	recent_jobs = frappe.get_all(
		"CRM POI Sync Job",
		fields=[
			"name",
			"status",
			"keywords",
			"city",
			"district",
			"total_fetched",
			"leads_created",
			"with_phone_count",
			"modified",
		],
		order_by="modified desc",
		limit_page_length=5,
	)

	return {
		"pending_call": pending_call,
		"contacted_today": contacted_today,
		"interested": interested,
		"new_leads": new_leads,
		"invalid": invalid,
		"recent_jobs": recent_jobs,
		"has_amap_enabled": bool(frappe.db.get_single_value("CRM Amap Settings", "enabled")),
	}
