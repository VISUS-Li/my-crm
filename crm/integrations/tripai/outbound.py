# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from crm.integrations.tripai.billing import resolve_billing_tripai_user_id, should_bill_for_sync


AI_OUTBOUND_FEATURE = "ai_outbound_call"
AI_OUTBOUND_CREDITS = 0.5


def request_ai_outbound_call(lead_name: str, script: str | None = None) -> dict[str, Any]:
	"""Queue an AI outbound screening call for a lead (Phase 5 foundation)."""
	lead = frappe.get_doc("CRM Lead", lead_name)
	frappe.has_permission("CRM Lead", "write", lead, throw=True)

	mobile = (lead.mobile_no or lead.phone or "").strip()
	if not mobile:
		frappe.throw(_("Lead has no phone number for AI outbound call"))

	tripai_user_id = resolve_billing_tripai_user_id(lead.lead_owner)
	settings = frappe.get_single("CRM Amap Settings")

	if should_bill_for_sync(settings) and tripai_user_id:
		try:
			from crm.integrations.tripai.client import delegated_credits_check, delegated_credits_consume

			check = delegated_credits_check(tripai_user_id, AI_OUTBOUND_CREDITS)
			if not check.get("available", check.get("sufficient")):
				frappe.throw(_("Insufficient TripAI credits for AI outbound call"))

			delegated_credits_consume(
				tripai_user_id,
				AI_OUTBOUND_CREDITS,
				feature_key=AI_OUTBOUND_FEATURE,
				description=_("AI outbound call for lead {0}").format(lead_name),
				metadata={"lead_name": lead_name, "mobile": mobile},
			)
		except ImportError:
			pass

	lead.db_set(
		{
			"status": _resolve_outbound_status(),
			"ai_call_summary": script or _("AI outbound call queued"),
		}
	)

	return {
		"success": True,
		"lead": lead_name,
		"status": lead.status,
		"message": _("AI outbound call queued. Full telephony integration is pending."),
	}


def apply_ai_outbound_callback(
	lead_name: str,
	*,
	score: int | None = None,
	summary: str | None = None,
	intent: str | None = None,
) -> dict[str, Any]:
	"""Apply AI outbound callback results to a lead."""
	lead = frappe.get_doc("CRM Lead", lead_name)

	updates: dict[str, Any] = {}
	if score is not None:
		updates["ai_call_score"] = score
	if summary:
		updates["ai_call_summary"] = summary

	status = intent or _status_from_score(score)
	if status and frappe.db.exists("CRM Lead Status", status):
		updates["status"] = status

	if updates:
		lead.db_set(updates)

	return {"success": True, "lead": lead_name, "status": lead.status}


def _resolve_outbound_status() -> str | None:
	if frappe.db.exists("CRM Lead Status", "AI已联系-低意向"):
		return "AI已联系-低意向"
	return None


def _status_from_score(score: int | None) -> str | None:
	if score is None:
		return None
	if score >= 70 and frappe.db.exists("CRM Lead Status", "AI已联系-高意向"):
		return "AI已联系-高意向"
	if frappe.db.exists("CRM Lead Status", "AI已联系-低意向"):
		return "AI已联系-低意向"
	return None
