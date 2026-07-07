"""Background tasks for Amap POI sync."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import now_datetime

from crm.amap.poi.client import build_client_from_settings
from crm.amap.poi.importer import POIImporter, promote_poi_to_lead
from crm.amap.poi.quadtree import BoundingBox, QuadTreeSplitter, bbox_from_string
from crm.amap.trace import finish_sync_segment, log_sync_event, start_sync_segment


def run_poi_sync(sync_job_name: str) -> None:
	frappe.cache().delete_value(f"poi_sync_cancel:{sync_job_name}")
	job = frappe.get_doc("CRM POI Sync Job", sync_job_name)
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
				"progress_message": _("Sync failed"),
			}
		)
		return

	job.db_set(
		{
			"status": "Running",
			"started_at": now_datetime(),
			"progress_message": _("Starting sync"),
			"daily_usage": 0,
		}
	)
	frappe.db.commit()
	log_sync_event(sync_job_name, "job_started", _("Starting sync"), {"keywords": job.keywords, "city": job.city})

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

			job.update_progress(_("Fetching POI data with quadtree..."))
			pois = []
			for keyword in split_keywords(job.keywords):
				if job.is_cancelled():
					break
				job.update_progress(_("Fetching POI data for keyword: {0}").format(keyword))
				segment = start_sync_segment(job, keyword=keyword, bbox=bounds.to_polygon())
				keyword_pois = splitter.quadtree_split(
						bounds,
						keywords=keyword,
						types=job.types or "",
						on_log=on_log,
					)
				pois.extend(keyword_pois)
				finish_sync_segment(segment, fetched_count=len(keyword_pois))
		else:
			job.update_progress(_("Fetching POI data via city text search..."))
			pois = _fetch_pois_by_text(client, job)

		if job.is_cancelled():
			job.db_set({"status": "Cancelled", "completed_at": now_datetime()})
			return

		job.update_progress(_("Importing {0} POI records...").format(len(pois)))
		log_sync_event(sync_job_name, "import_started", _("Importing {0} POI records...").format(len(pois)))
		importer.process_pois(pois)

		job.db_set(
			{
				"status": "Completed",
				"completed_at": now_datetime(),
				"total_fetched": importer.stats["total_fetched"],
				"with_phone_count": importer.stats["with_phone_count"],
				"leads_created": importer.stats["leads_created"],
				"leads_skipped": importer.stats["leads_skipped"],
				"progress_message": _("Sync completed successfully"),
			}
		)
		frappe.db.commit()
		log_sync_event(
			sync_job_name,
			"job_completed",
			_("Sync completed successfully"),
			{
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
				"progress_message": _("Sync failed"),
			}
		)
		log_sync_event(sync_job_name, "job_failed", _("Sync failed"), {"error": error_log})


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


def _fetch_pois_by_text(client, job) -> list:
	all_pois = []
	for keyword in split_keywords(job.keywords):
		segment = start_sync_segment(job, keyword=keyword)
		segment_pois = []
		reported_count = 0
		page_count = 0
		error_message = ""
		page = 1
		while page <= 8:
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
				break
			reported_count = max(reported_count, result.count or 0)
			page_count = page
			segment_pois.extend(result.data)
			if len(result.data) < 25:
				break
			page += 1
		all_pois.extend(segment_pois)
		finish_sync_segment(
			segment,
			status="Failed" if error_message else "Completed",
			fetched_count=len(segment_pois),
			reported_count=reported_count,
			page_count=page_count,
			api_calls=page_count,
			truncated=bool(reported_count and reported_count > len(segment_pois)),
			error_message=error_message,
		)
	return all_pois


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
