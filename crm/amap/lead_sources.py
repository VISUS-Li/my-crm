"""Default CRM Lead Source records for Amap POI sync."""

from __future__ import annotations

import frappe

AMAP_LEAD_SOURCES = (
	"高德地图",
	"高德地图-餐饮",
	"高德地图-美容",
	"高德地图-教培",
	"高德地图-零售",
)

DEFAULT_AMAP_LEAD_SOURCE = AMAP_LEAD_SOURCES[0]


def ensure_lead_source(source_name: str | None) -> str | None:
	if not source_name:
		return None

	if frappe.db.exists("CRM Lead Source", source_name):
		return source_name

	frappe.get_doc({"doctype": "CRM Lead Source", "source_name": source_name}).insert(
		ignore_permissions=True
	)
	return source_name


def ensure_amap_lead_sources() -> None:
	for source_name in AMAP_LEAD_SOURCES:
		ensure_lead_source(source_name)
