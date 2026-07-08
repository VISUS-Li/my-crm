"""Background tasks for Amap POI sync."""

from __future__ import annotations

from dataclasses import dataclass

import frappe
from frappe import _
from frappe.utils import now_datetime

from crm.amap.poi.client import build_client_from_settings
from crm.amap.poi.importer import POIImporter, promote_poi_to_lead
from crm.amap.poi.quadtree import AmapSearchError, BoundingBox, QuadTreeSplitter, bbox_from_string
from crm.amap.trace import finish_sync_segment, log_sync_event, start_sync_segment


SYNC_FAILED = "同步失败"
SYNC_STARTING = "正在启动同步"
SYNC_COMPLETED = "同步成功完成"
SYNC_PARTIAL = "部分同步完成"
MAX_TEXT_SEARCH_PAGES = 8


@dataclass
class FetchSummary:
	pois: list[dict]
	had_errors: bool = False
	truncated: bool = False


def run_poi_sync(sync_job_name: str) -> None:
	job = frappe.get_doc("CRM POI Sync Job", sync_job_name)
	cancel_key = f"poi_sync_cancel:{sync_job_name}"
	if job.status == "Cancelled" or frappe.cache().get_value(cancel_key):
		job.db_set({"status": "Cancelled", "completed_at": now_datetime()})
		frappe.cache().delete_value(cancel_key)
		return
	frappe.cache().delete_value(cancel_key)
	settings = frappe.get_single("CRM Amap Settings")

	if not settings.enabled:
		job.db_set(
			{
				"status": "Failed",
				"error_log": _("Amap POI sync is disabled in settings"),
				"completed_at": now_datetime(),
			}
		)
		return

	tripai_user_id = _resolve_job_tripai_user(job)

	try:
		_pre_sync_billing_check(job, tripai_user_id, settings)
	except Exception as exc:
		error_log = str(exc)
		try:
			from crm.integrations.tripai.billing import InsufficientCreditsError

			if isinstance(exc, InsufficientCreditsError):
				error_log = _("Insufficient TripAI credits. Required: {0}. Please recharge on the platform.").format(
					exc.required
				)
		except ImportError:
			pass
		job.db_set(
			{
				"status": "Failed",
				"completed_at": now_datetime(),
				"error_log": error_log,
				"progress_message": SYNC_FAILED,
			}
		)
		return

	job.db_set(
		{
			"status": "Running",
			"started_at": now_datetime(),
			"progress_message": SYNC_STARTING,
			"daily_usage": 0,
		}
	)
	frappe.db.commit()
	log_sync_event(sync_job_name, "job_started", SYNC_STARTING, {"keywords": job.keywords, "city": job.city})

	try:
		client = build_client_from_settings(settings, tripai_user_id=tripai_user_id, job_name=sync_job_name)
		importer = POIImporter(job, settings, tripai_user_id=tripai_user_id)

		_ensure_job_adcode(job, client)

		if job.bbox or job.adcode:
			splitter = QuadTreeSplitter(
				client,
				poi_threshold=settings.poi_threshold or 180,
				max_depth=settings.max_recursion_depth or 20,
			)

			bounds = _resolve_bounds(job, client)
			if not bounds:
				raise ValueError(_("Unable to resolve search bounds from bbox or adcode."))

			def on_log(message: str):
				if job.is_cancelled():
					splitter.cancel()
					return
				job.update_progress(message)

			if job.is_cancelled():
				job.db_set({"status": "Cancelled", "completed_at": now_datetime()})
				return

			job.update_progress("正在使用四叉树获取 POI 数据...")
			pois = []
			truncated = False
			for keyword in split_keywords(job.keywords):
				if job.is_cancelled():
					break
				job.update_progress("正在获取关键词「{0}」的 POI 数据".format(keyword))
				segment = start_sync_segment(job, keyword=keyword, bbox=bounds.to_polygon())
				try:
					keyword_pois = splitter.quadtree_split(
						bounds,
						keywords=keyword,
						types=job.types or "",
						on_log=on_log,
					)
				except AmapSearchError as exc:
					finish_sync_segment(
						segment,
						status="Failed",
						error_code=exc.code,
						error_message=str(exc),
					)
					log_sync_event(
						sync_job_name,
						"segment_failed",
						_("POI sync segment failed"),
						{"keyword": keyword, "error": str(exc), "code": exc.code},
						segment=segment,
					)
					raise
				keyword_pois = _filter_pois_for_job_region(keyword_pois, job)
				pois.extend(keyword_pois)
				finish_sync_segment(segment, fetched_count=len(keyword_pois))
		else:
			job.update_progress("正在通过城市文本搜索获取 POI 数据...")
			fetch_summary = _fetch_pois_by_text(client, job)
			pois = fetch_summary.pois
			truncated = fetch_summary.truncated

		if job.is_cancelled():
			job.db_set({"status": "Cancelled", "completed_at": now_datetime()})
			return

		import_message = "正在导入 {0} 条 POI 记录...".format(len(pois))
		job.update_progress(import_message)
		log_sync_event(sync_job_name, "import_started", import_message)
		importer.process_pois(pois)

		final_status = "Completed"
		final_message = SYNC_COMPLETED
		if "fetch_summary" in locals() and fetch_summary.had_errors:
			final_status = "Partial" if pois else "Failed"
			final_message = SYNC_PARTIAL if pois else SYNC_FAILED
		elif truncated:
			final_status = "Partial"
			final_message = SYNC_PARTIAL

		job.db_set(
			{
				"status": final_status,
				"completed_at": now_datetime(),
				"total_fetched": importer.stats["total_fetched"],
				"with_phone_count": importer.stats["with_phone_count"],
				"leads_created": importer.stats["leads_created"],
				"leads_skipped": importer.stats["leads_skipped"],
				"progress_message": final_message,
			}
		)
		frappe.db.commit()
		log_sync_event(
			sync_job_name,
			"job_completed",
			final_message,
			{
				"status": final_status,
				"total_fetched": importer.stats["total_fetched"],
				"with_phone_count": importer.stats["with_phone_count"],
				"leads_created": importer.stats["leads_created"],
				"leads_skipped": importer.stats["leads_skipped"],
			},
		)
	except Exception as exc:
		frappe.log_error(title=f"POI Sync Job failed: {sync_job_name}", message=frappe.get_traceback())
		error_log = str(exc)
		try:
			from crm.integrations.tripai.billing import InsufficientCreditsError

			if isinstance(exc, InsufficientCreditsError):
				error_log = _("Insufficient TripAI credits. Required: {0}. Please recharge on the platform.").format(
					exc.required
				)
		except ImportError:
			pass
		job.db_set(
			{
				"status": "Failed",
				"completed_at": now_datetime(),
				"error_log": error_log,
				"progress_message": SYNC_FAILED,
			}
		)
		log_sync_event(sync_job_name, "job_failed", SYNC_FAILED, {"error": error_log})


def _ensure_job_adcode(job, client) -> None:
	"""Resolve adcode when user picked a district in the region picker but adcode is empty.

	City-only jobs intentionally skip adcode so sync uses lightweight text search
	instead of quadtree over an entire municipality.
	"""
	if job.adcode or job.bbox:
		return

	if not job.district:
		return

	query_parts = [job.district, job.city, job.province]
	query = next((part for part in query_parts if part), None)
	if not query:
		return

	districts = client.search_districts(keywords=query, subdistrict=0)
	if not districts:
		return

	match = districts[0]
	adcode = match.get("adcode")
	if not adcode:
		return

	job.db_set("adcode", adcode)
	frappe.db.commit()


def _resolve_bounds(job, client) -> BoundingBox | None:
	if job.bbox:
		return bbox_from_string(job.bbox)

	if job.adcode:
		bbox = client.get_district_bbox(job.adcode)
		if bbox:
			return BoundingBox(*bbox)

	return None


def _fetch_pois_by_text(client, job) -> FetchSummary:
	all_pois = []
	had_errors = False
	any_truncated = False
	for keyword in split_keywords(job.keywords):
		if job.is_cancelled():
			break
		segment = start_sync_segment(job, keyword=keyword)
		segment_pois = []
		reported_count = 0
		page_count = 0
		error_message = ""
		page = 1
		while page <= MAX_TEXT_SEARCH_PAGES:
			if job.is_cancelled():
				break
			result = client.search_text(
				keywords=keyword,
				city=job.city,
				types=job.types or "",
				limit=25,
				page=page,
				citylimit=True,
			)
			if not result.success or not result.data:
				error_message = result.error_message if not result.success else ""
				had_errors = bool(error_message) or had_errors
				break
			reported_count = max(reported_count, result.count or 0)
			page_count = page
			segment_pois.extend(result.data)
			if len(result.data) < 25:
				break
			page += 1
		segment_pois = _filter_pois_for_job_region(segment_pois, job)
		segment_truncated = bool(reported_count and reported_count > len(segment_pois))
		any_truncated = any_truncated or segment_truncated
		all_pois.extend(segment_pois)
		finish_sync_segment(
			segment,
			status="Failed" if error_message else "Completed",
			fetched_count=len(segment_pois),
			reported_count=reported_count,
			page_count=page_count,
			api_calls=page_count,
			truncated=segment_truncated,
			error_message=error_message,
		)
	return FetchSummary(pois=all_pois, had_errors=had_errors, truncated=any_truncated)


def _filter_pois_for_job_region(pois: list[dict], job) -> list[dict]:
	"""Keep bbox/adcode searches from importing nearby POIs outside the chosen district."""
	adcode = (getattr(job, "adcode", None) or "").strip()
	district = (getattr(job, "district", None) or "").strip()
	if not adcode and not district:
		return pois

	filtered = []
	for poi in pois:
		poi_adcode = str(poi.get("adcode") or "").strip()
		poi_district = str(poi.get("adname") or poi.get("district") or "").strip()
		if adcode and poi_adcode == adcode:
			filtered.append(poi)
		elif not adcode and district and poi_district == district:
			filtered.append(poi)
	return filtered


def split_keywords(keywords: str | None) -> list[str]:
	if not keywords:
		return [""]

	parts: list[str] = []
	for delimiter in ("|", ",", "，", ";", "；", "\n"):
		keywords = keywords.replace(delimiter, "|")
	for part in keywords.split("|"):
		part = part.strip()
		if part and part not in parts:
			parts.append(part)
	return parts or [""]


def promote_poi_record_to_lead(poi_record_name: str) -> str:
	return promote_poi_to_lead(poi_record_name)


def _resolve_job_tripai_user(job) -> str | None:
	owner = job.job_owner or frappe.session.user
	try:
		from crm.integrations.tripai.billing import resolve_billing_tripai_user_id

		return resolve_billing_tripai_user_id(owner)
	except Exception:
		return None


def _pre_sync_billing_check(job, tripai_user_id: str | None, settings) -> None:
	try:
		from crm.integrations.tripai.billing import (
			InsufficientCreditsError,
			RuntimeConfigError,
			check_credits_for_sync,
			should_bill_for_sync,
		)
	except ImportError:
		return

	if not should_bill_for_sync(settings):
		return

	if not tripai_user_id:
		raise RuntimeConfigError(_("TripAI billing account is not linked for this job owner"))

	# Conservative estimate: 50 API calls + 100 POI imports
	result = check_credits_for_sync(tripai_user_id, estimated_api_calls=50, estimated_poi_imports=100)
	if not result.get("sufficient"):
		raise InsufficientCreditsError(result.get("required", 0), result.get("balance"))
