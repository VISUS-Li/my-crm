# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


class CRMPOISyncJob(Document):
	def validate(self):
		if self.is_new() and (not self.job_owner or self.job_owner == "__user__"):
			self.job_owner = frappe.session.user

		if not self.agent_tenant_id:
			from crm.permissions.agent_tenant import resolve_agent_tenant_id

			self.agent_tenant_id = resolve_agent_tenant_id(self.job_owner)

		if self.bbox:
			parts = [p.strip() for p in self.bbox.split(",")]
			if len(parts) != 4:
				frappe.throw(_("Bounding box must be min_lng,min_lat,max_lng,max_lat"))

	@frappe.whitelist()
	def start_sync(self):
		if self.status in ("Running", "Queued"):
			frappe.throw(_("Sync is already running or queued"))

		if self.status == "Completed":
			self._reset_stats()

		self._ensure_agent_tenant_id()
		self._check_tripai_license_before_start()
		self._check_tripai_credits_before_start()

		self.db_set(
			{
				"status": "Queued",
				"progress_message": _("Queued for processing"),
				"error_log": "",
			}
		)

		frappe.enqueue(
			"crm.amap.tasks.run_poi_sync",
			queue="long",
			timeout=7200,
			job_name=f"poi_sync_{self.name}",
			enqueue_after_commit=True,
			sync_job_name=self.name,
		)

		return {"status": "Queued"}

	@frappe.whitelist()
	def cancel_sync(self):
		if self.status not in ("Running", "Queued"):
			frappe.throw(_("Only running or queued jobs can be cancelled"))

		frappe.cache().set_value(f"poi_sync_cancel:{self.name}", 1, expires_in_sec=7200)
		self.db_set({"status": "Cancelled", "completed_at": now_datetime()})
		return {"status": "Cancelled"}

	def _reset_stats(self):
		self.db_set(
			{
				"total_fetched": 0,
				"with_phone_count": 0,
				"leads_created": 0,
				"leads_skipped": 0,
				"started_at": None,
				"completed_at": None,
				"progress_message": "",
				"error_log": "",
			}
		)

	def is_cancelled(self) -> bool:
		return bool(frappe.cache().get_value(f"poi_sync_cancel:{self.name}"))

	def _ensure_agent_tenant_id(self) -> None:
		if self.agent_tenant_id:
			return
		from crm.permissions.agent_tenant import resolve_agent_tenant_id

		tenant_id = resolve_agent_tenant_id(self.job_owner)
		if tenant_id:
			self.db_set("agent_tenant_id", tenant_id)

	def _check_tripai_license_before_start(self) -> None:
		try:
			from crm.integrations.tripai.license import LicenseNotEntitledError, ensure_user_licensed
		except ImportError:
			return

		try:
			ensure_user_licensed(self.job_owner)
		except LicenseNotEntitledError:
			raise

	def _check_tripai_credits_before_start(self) -> None:
		try:
			from crm.integrations.tripai.billing import (
				InsufficientCreditsError,
				check_credits_for_sync,
				resolve_billing_tripai_user_id,
				should_bill_for_sync,
			)
		except ImportError:
			return

		settings = frappe.get_single("CRM Amap Settings")
		if not should_bill_for_sync(settings):
			return

		tripai_user_id = resolve_billing_tripai_user_id(self.job_owner)
		if not tripai_user_id:
			frappe.throw(
				_("TripAI account is not linked. Please log in via the TripAI platform first."),
				title=_("TripAI Not Linked"),
			)

		result = check_credits_for_sync(tripai_user_id, estimated_api_calls=50, estimated_poi_imports=100)
		if not result.get("sufficient"):
			raise InsufficientCreditsError(result.get("required", 0), result.get("balance"))

	def update_progress(self, message: str):
		self.db_set("progress_message", message[:500])
		frappe.db.commit()

	def update_stats(
		self,
		total_fetched: int | None = None,
		with_phone_count: int | None = None,
		leads_created: int | None = None,
		leads_skipped: int | None = None,
	):
		data = {}
		if total_fetched is not None:
			data["total_fetched"] = total_fetched
		if with_phone_count is not None:
			data["with_phone_count"] = with_phone_count
		if leads_created is not None:
			data["leads_created"] = leads_created
		if leads_skipped is not None:
			data["leads_skipped"] = leads_skipped
		if data:
			self.db_set(data)
			frappe.db.commit()
