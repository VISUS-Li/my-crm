"""Whitelist API endpoints for Amap POI sync."""

from __future__ import annotations

import frappe
from frappe import _

from crm.amap.poi.client import build_client_from_settings


@frappe.whitelist()
def test_connection(api_key: str = ""):
	"""Test Amap Web服务 API key. Pass api_key to test unsaved form values."""
	from crm.amap.poi.client import AmapClient, build_client_from_settings

	settings = frappe.get_single("CRM Amap Settings")

	if settings.use_mock_api and not (api_key and api_key.strip()):
		return {"success": True, "message": _("Mock API mode enabled")}

	if api_key and api_key.strip():
		client = AmapClient(
			api_keys=[api_key.strip()],
			request_interval=settings.request_interval or 0.35,
			use_mock=False,
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
		try:
			from crm.integrations.tripai.billing import InsufficientCreditsError
			from crm.integrations.tripai.settings import get_tripai_settings

			if isinstance(exc, InsufficientCreditsError):
				settings = get_tripai_settings()
				frappe.throw(
					_(
						"Insufficient TripAI credits. Required: {0}, balance: {1}. Recharge at {2}"
					).format(
						exc.required,
						exc.balance if exc.balance is not None else _("unknown"),
						f"{settings['base_url']}/zh/dashboard",
					),
					title=_("Insufficient TripAI Credits"),
					exc=frappe.ValidationError,
				)
		except ImportError:
			pass
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
	return {
		"name": job.name,
		"status": job.status,
		"total_fetched": job.total_fetched,
		"with_phone_count": job.with_phone_count,
		"leads_created": job.leads_created,
		"leads_skipped": job.leads_skipped,
		"progress_message": job.progress_message,
		"error_log": job.error_log,
		"started_at": job.started_at,
		"completed_at": job.completed_at,
	}


@frappe.whitelist()
def preview_search(keywords: str, city: str, types: str = "", limit: int = 10):
	settings = frappe.get_single("CRM Amap Settings")
	if not settings.enabled and not settings.use_mock_api:
		frappe.throw(_("Enable Amap POI sync or mock mode in settings first"))

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
def promote_poi_to_lead(poi_record_name: str):
	from crm.amap.tasks import promote_poi_record_to_lead

	frappe.has_permission("CRM POI Record", "write", throw=True)
	return promote_poi_record_to_lead(poi_record_name)


@frappe.whitelist(allow_guest=True)
def ai_call_callback():
	"""Phase 3 placeholder for outbound call platform webhook."""
	frappe.throw(_("AI outbound callback is not configured yet"), frappe.ValidationError)
