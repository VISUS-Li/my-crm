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

		self._check_tripai_credits_before_start()

		self.db_set(
			{
				"status": "Queued",
				"progress_message": "Queued for processing",
				"error_log": "",
			}
		)

		frappe.enqueue(
			"crm.amap.tasks.run_poi_sync",
			queue="long",
			timeout=7200,
			job_name=self.name,
			enqueue_after_commit=True,
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

	def _check_tripai_credits_before_start(self) -> None:
		try:
			from crm.integrations.tripai.billing import (
				InsufficientCreditsError,
				check_credits_for_sync,
				resolve_tripai_user_id,
				should_bill_for_sync,
			)
		except ImportError:
			return

		settings = frappe.get_single("CRM Amap Settings")
		if not should_bill_for_sync(settings):
			return

		tripai_user_id = resolve_tripai_user_id(self.job_owner)
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
