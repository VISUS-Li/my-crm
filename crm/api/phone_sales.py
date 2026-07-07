"""APIs for phone-sales / merchant outreach workflow."""

from __future__ import annotations

import frappe
from frappe.utils import getdate, nowdate

from crm.api.session import get_session_role_flags
from crm.utils import is_frappe_version

COUNT_NAME = (
	{"COUNT": "name", "as": "total_count"}
	if is_frappe_version("16", above=True)
	else "count(name) as total_count"
)

_POI_JOB_FIELDS = [
	"name",
	"status",
	"keywords",
	"city",
	"district",
	"total_fetched",
	"leads_created",
	"with_phone_count",
	"modified",
]


def _amap_lead_filters() -> list:
	return [
		["CRM Lead", "converted", "=", 0],
		["CRM Lead", "source", "like", "%高德%"],
	]


def _count_permitted_leads(extra_filters: list) -> int:
	"""Count CRM Leads visible to the current user (permission-aware)."""
	rows = frappe.get_list(
		"CRM Lead",
		filters=_amap_lead_filters() + extra_filters,
		fields=[COUNT_NAME],
	)
	if not rows:
		return 0
	return int(rows[0].total_count or 0)


def _get_permitted_recent_jobs(limit: int = 5) -> list[dict]:
	"""Recent POI sync jobs visible to the current user (permission-aware)."""
	return frappe.get_list(
		"CRM POI Sync Job",
		fields=_POI_JOB_FIELDS,
		order_by="modified desc",
		limit_page_length=limit,
	)


@frappe.whitelist()
def get_workbench_stats():
	"""Summary counts for the phone-sales workbench dashboard."""
	get_session_role_flags()
	today = getdate(nowdate())

	pending_call = _count_permitted_leads(
		[
			["CRM Lead", "status", "=", "待拨打"],
			["CRM Lead", "has_valid_phone", "=", 1],
		]
	)

	interested = _count_permitted_leads([["CRM Lead", "status", "=", "有意向"]])

	new_leads = _count_permitted_leads([["CRM Lead", "status", "=", "新线索"]])

	contacted_today = _count_permitted_leads(
		[
			["CRM Lead", "status", "=", "已联系"],
			["CRM Lead", "modified", "between", [today, today]],
		]
	)

	invalid = _count_permitted_leads([["CRM Lead", "status", "=", "无效"]])

	return {
		"pending_call": pending_call,
		"contacted_today": contacted_today,
		"interested": interested,
		"new_leads": new_leads,
		"invalid": invalid,
		"recent_jobs": _get_permitted_recent_jobs(),
		"has_amap_enabled": bool(frappe.db.get_single_value("CRM Amap Settings", "enabled")),
	}
