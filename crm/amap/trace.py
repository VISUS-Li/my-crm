"""Trace helpers for Amap POI sync jobs."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import now_datetime


def log_sync_event(
	sync_job: str,
	event_type: str,
	message: str = "",
	payload: dict[str, Any] | None = None,
	segment: str | None = None,
) -> str | None:
	try:
		doc = frappe.get_doc(
			{
				"doctype": "CRM POI Sync Event",
				"naming_series": "POI-EVENT-.YYYY.-.#####",
				"sync_job": sync_job,
				"segment": segment,
				"event_type": event_type,
				"message": message[:500] if message else "",
				"payload_json": json.dumps(payload or {}, ensure_ascii=False),
			}
		)
		doc.insert(ignore_permissions=True)
		return doc.name
	except Exception:
		return None


def start_sync_segment(sync_job, keyword: str = "", bbox: str = "") -> str | None:
	try:
		doc = frappe.get_doc(
			{
				"doctype": "CRM POI Sync Segment",
				"naming_series": "POI-SEG-.YYYY.-.#####",
				"sync_job": sync_job.name,
				"keyword": keyword,
				"types": sync_job.types or "",
				"status": "Running",
				"province": sync_job.province,
				"city": sync_job.city,
				"district": sync_job.district,
				"adcode": sync_job.adcode,
				"bbox": bbox or sync_job.bbox or "",
				"started_at": now_datetime(),
			}
		)
		doc.insert(ignore_permissions=True)
		log_sync_event(
			sync_job.name,
			"segment_started",
			"同步分段开始",
			{"keyword": keyword, "types": sync_job.types or "", "bbox": bbox or sync_job.bbox or ""},
			segment=doc.name,
		)
		return doc.name
	except Exception:
		return None


def finish_sync_segment(
	segment: str | None,
	status: str = "Completed",
	fetched_count: int = 0,
	reported_count: int = 0,
	page_count: int = 0,
	api_calls: int = 0,
	truncated: bool = False,
	error_code: str = "",
	error_message: str = "",
) -> None:
	if not segment:
		return
	try:
		frappe.db.set_value(
			"CRM POI Sync Segment",
			segment,
			{
				"status": status,
				"fetched_count": fetched_count,
				"reported_count": reported_count,
				"page_count": page_count,
				"api_calls": api_calls,
				"truncated": 1 if truncated else 0,
				"error_code": error_code,
				"error_message": error_message[:500] if error_message else "",
				"completed_at": now_datetime(),
			},
		)
	except Exception:
		return
