"""Whitelist API endpoints for Amap POI sync."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import now_datetime

from crm.amap.poi.client import build_client_from_settings
from crm.amap.trace import log_sync_event


@frappe.whitelist()
def test_connection(api_key: str = ""):
	"""Test Amap Web服务 API key. Pass api_key to test unsaved form values."""
	from crm.amap.poi.client import AmapClient, build_client_from_settings

	settings = frappe.get_single("CRM Amap Settings")

	if api_key and api_key.strip():
		client = AmapClient(
			api_keys=[api_key.strip()],
			request_interval=settings.request_interval or 0.35,
		)
		return client.test_connection()

	return build_client_from_settings(settings).test_connection()


@frappe.whitelist()
def start_sync_job(job_name: str):
	job = frappe.get_doc("CRM POI Sync Job", job_name)
	frappe.has_permission("CRM POI Sync Job", "write", job, throw=True)
	try:
		return job.start_sync()
	except Exception as exc:
		def mark_start_failed(message: str):
			try:
				job.db_set(
					{
						"status": "Failed",
						"completed_at": now_datetime(),
						"error_log": message,
						"progress_message": _("Sync failed"),
					}
				)
				log_sync_event(job.name, "job_start_failed", _("Sync failed"), {"error": message})
				frappe.db.commit()
			except Exception:
				pass

		try:
			from crm.integrations.tripai.billing import InsufficientCreditsError, RuntimeConfigError
			from crm.integrations.tripai.license import LicenseNotEntitledError
			from crm.integrations.tripai.settings import get_tripai_settings

			if isinstance(exc, LicenseNotEntitledError):
				message = str(exc)
				mark_start_failed(message)
				frappe.throw(
					message,
					title=_("TripAI License Required"),
					exc=frappe.ValidationError,
				)

			if isinstance(exc, InsufficientCreditsError):
				settings = get_tripai_settings()
				message = _(
					"Insufficient TripAI credits. Required: {0}, balance: {1}. Recharge at {2}"
				).format(
					exc.required,
					exc.balance if exc.balance is not None else _("unknown"),
					f"{settings['base_url']}/zh/dashboard",
				)
				mark_start_failed(message)
				frappe.throw(
					message,
					title=_("Insufficient TripAI Credits"),
					exc=frappe.ValidationError,
				)

			if isinstance(exc, RuntimeConfigError):
				mark_start_failed(str(exc))
				frappe.throw(str(exc), title=_("TripAI Configuration Error"), exc=frappe.ValidationError)
		except ImportError:
			pass
		mark_start_failed(str(exc))
		raise


@frappe.whitelist()
def cancel_sync_job(job_name: str):
	job = frappe.get_doc("CRM POI Sync Job", job_name)
	frappe.has_permission("CRM POI Sync Job", "write", job, throw=True)
	return job.cancel_sync()


@frappe.whitelist()
def get_job_progress(job_name: str):
	job = frappe.get_doc("CRM POI Sync Job", job_name)
	frappe.has_permission("CRM POI Sync Job", "read", job, throw=True)
	events = []
	segments = []
	try:
		events = frappe.get_all(
			"CRM POI Sync Event",
			filters={"sync_job": job_name},
			fields=["name", "event_type", "message", "segment", "payload_json", "creation"],
			order_by="creation desc",
			limit=20,
		)
	except Exception:
		events = []
	try:
		segments = frappe.get_all(
			"CRM POI Sync Segment",
			filters={"sync_job": job_name},
			fields=[
				"name",
				"keyword",
				"status",
				"reported_count",
				"fetched_count",
				"page_count",
				"truncated",
				"error_message",
			],
			order_by="creation desc",
			limit=50,
		)
	except Exception:
		segments = []
	return {
		"name": job.name,
		"status": job.status,
		"keywords": job.keywords,
		"city": job.city,
		"district": job.district,
		"job_owner": job.job_owner,
		"total_fetched": job.total_fetched,
		"with_phone_count": job.with_phone_count,
		"leads_created": job.leads_created,
		"leads_skipped": job.leads_skipped,
		"progress_message": job.progress_message,
		"error_log": job.error_log,
		"started_at": job.started_at,
		"completed_at": job.completed_at,
		"events": events,
		"segments": segments,
	}


@frappe.whitelist()
def preview_search(keywords: str, city: str, types: str = "", limit: int = 10):
	settings = frappe.get_single("CRM Amap Settings")
	if not settings.enabled:
		frappe.throw(_("Enable Amap POI sync in settings first"))

	client = build_client_from_settings(settings)
	result = client.search_text(
		keywords=keywords,
		city=city,
		types=types,
		limit=int(limit or 10),
		page=1,
	)
	if not result.success:
		frappe.throw(result.error_message or _("Preview search failed"))

	return {
		"count": result.count,
		"pois": result.data,
	}


@frappe.whitelist()
def get_districts(keywords: str = "", adcode: str = "", subdistrict: int = 1):
	"""Return province/city/district options for the region picker."""
	settings = frappe.get_single("CRM Amap Settings")
	if not settings.enabled:
		frappe.throw(_("Enable Amap POI sync in settings first"))

	client = build_client_from_settings(settings)
	return client.search_districts(
		keywords=keywords or "",
		adcode=adcode or "",
		subdistrict=int(subdistrict or 1),
	)


@frappe.whitelist()
def list_job_poi_records(job_name: str, page: int = 1, page_length: int = 20):
	job = frappe.get_doc("CRM POI Sync Job", job_name)
	frappe.has_permission("CRM POI Sync Job", "read", job, throw=True)

	page = max(int(page or 1), 1)
	page_length = min(max(int(page_length or 20), 1), 100)
	start = (page - 1) * page_length

	records = frappe.get_all(
		"CRM POI Record",
		filters={"sync_job": job_name},
		fields=[
			"name",
			"name1",
			"tel",
			"tel_normalized",
			"all_phones",
			"has_valid_phone",
			"website",
			"email",
			"address",
			"city",
			"district",
			"poi_type",
			"rating",
			"cost",
			"primary_photo_url",
			"photo_count",
			"sync_action",
			"skip_reason",
			"lead",
		],
		order_by="modified desc",
		start=start,
		limit=page_length,
	)
	total = frappe.db.count("CRM POI Record", {"sync_job": job_name})

	return {
		"records": records,
		"total": total,
		"page": page,
		"page_length": page_length,
	}


@frappe.whitelist()
def promote_poi_to_lead(poi_record_name: str):
	from crm.amap.tasks import promote_poi_record_to_lead

	frappe.has_permission("CRM POI Record", "write", throw=True)
	return promote_poi_record_to_lead(poi_record_name)


@frappe.whitelist(allow_guest=True)
def ai_call_callback():
	"""Phase 3 placeholder for outbound call platform webhook."""
	frappe.throw(_("AI outbound callback is not configured yet"), frappe.ValidationError)
