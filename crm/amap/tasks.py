"""Background tasks for Amap POI sync."""

from __future__ import annotations

import frappe
from frappe.utils import now_datetime

from crm.amap.poi.client import build_client_from_settings
from crm.amap.poi.importer import POIImporter, promote_poi_to_lead
from crm.amap.poi.quadtree import BoundingBox, QuadTreeSplitter, bbox_from_string


def run_poi_sync(job_name: str) -> None:
	frappe.cache().delete_value(f"poi_sync_cancel:{job_name}")
	job = frappe.get_doc("CRM POI Sync Job", job_name)
	settings = frappe.get_single("CRM Amap Settings")

	if not settings.enabled and not settings.use_mock_api:
		job.db_set(
			{
				"status": "Failed",
				"error_log": "Amap POI sync is disabled in settings",
				"completed_at": now_datetime(),
			}
		)
		return

	job.db_set({"status": "Running", "started_at": now_datetime(), "progress_message": "Starting sync"})
	frappe.db.commit()

	try:
		client = build_client_from_settings(settings)
		importer = POIImporter(job, settings)

		if job.bbox or job.adcode:
			splitter = QuadTreeSplitter(
				client,
				poi_threshold=settings.poi_threshold or 180,
				max_depth=settings.max_recursion_depth or 20,
			)

			bounds = _resolve_bounds(job, client)
			if not bounds:
				raise ValueError("Unable to resolve search bounds from bbox or adcode.")

			def on_log(message: str):
				if job.is_cancelled():
					splitter.cancel()
					return
				job.update_progress(message)

			if job.is_cancelled():
				job.db_set({"status": "Cancelled", "completed_at": now_datetime()})
				return

			job.update_progress("Fetching POI data with quadtree...")
			pois = splitter.quadtree_split(
				bounds,
				keywords=job.keywords,
				types=job.types or "",
				on_log=on_log,
			)
		else:
			job.update_progress("Fetching POI data via city text search...")
			pois = _fetch_pois_by_text(client, job)

		if job.is_cancelled():
			job.db_set({"status": "Cancelled", "completed_at": now_datetime()})
			return

		job.update_progress(f"Importing {len(pois)} POI records...")
		importer.process_pois(pois)

		job.db_set(
			{
				"status": "Completed",
				"completed_at": now_datetime(),
				"total_fetched": importer.stats["total_fetched"],
				"with_phone_count": importer.stats["with_phone_count"],
				"leads_created": importer.stats["leads_created"],
				"leads_skipped": importer.stats["leads_skipped"],
				"progress_message": "Sync completed successfully",
			}
		)
	except Exception as exc:
		frappe.log_error(title=f"POI Sync Job failed: {job_name}", message=frappe.get_traceback())
		job.db_set(
			{
				"status": "Failed",
				"completed_at": now_datetime(),
				"error_log": str(exc),
				"progress_message": "Sync failed",
			}
		)


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
	page = 1
	while page <= 8:
		result = client.search_text(
			keywords=job.keywords,
			city=job.city,
			types=job.types or "",
			limit=25,
			page=page,
		)
		if not result.success or not result.data:
			break
		all_pois.extend(result.data)
		if len(result.data) < 25:
			break
		page += 1
	return all_pois


def promote_poi_record_to_lead(poi_record_name: str) -> str:
	return promote_poi_to_lead(poi_record_name)
