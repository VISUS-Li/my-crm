# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from crm.integrations.tripai.client import (
	TripAIAPIError,
	TripAIConfigError,
	delegated_credits_check,
	delegated_credits_consume,
	fetch_runtime_config,
)
from crm.integrations.tripai.settings import get_tripai_settings


def is_billing_enabled() -> bool:
	try:
		settings = get_tripai_settings()
	except TripAIConfigError:
		return False
	return bool(settings["enabled"] and settings["runtime_token"])


def should_bill_for_sync(settings=None) -> bool:
	"""Billing applies only when TripAI is enabled and CRM is not in mock mode."""
	if settings is None:
		settings = frappe.get_single("CRM Amap Settings")
	if bool(getattr(settings, "use_mock_api", False)):
		return False
	return is_billing_enabled()


def get_runtime_amap_keys(user_id: str | None = None) -> list[str]:
	"""Fetch Amap API keys from TripAI tool-config runtime (secret1..secret3).

	Admin secrets are project-level; do not pass userId to the runtime API (requires session token).
	"""
	_ = user_id  # reserved for future per-user key overrides
	if not is_billing_enabled():
		return []

	try:
		payload = fetch_runtime_config()
	except TripAIAPIError as exc:
		frappe.log_error(title="TripAI runtime config fetch failed", message=str(exc))
		return []

	config = payload.get("config") or {}
	keys: list[str] = []
	for field in ("secret1", "secret2", "secret3"):
		value = config.get(field)
		if isinstance(value, str) and value.strip():
			keys.append(value.strip())
	return keys


def get_billing_rates(user_id: str | None = None) -> dict[str, float]:
	_ = user_id
	if not is_billing_enabled():
		return {"api_call": 0.0, "poi_import": 0.0}

	try:
		payload = fetch_runtime_config()
	except TripAIAPIError:
		return {"api_call": 0.02, "poi_import": 0.1}

	config = payload.get("config") or {}
	return {
		"api_call": float(config.get("config1") or 0.02),
		"poi_import": float(config.get("config2") or 0.1),
	}


def resolve_tripai_user_id(crm_user: str | None = None) -> str | None:
	crm_user = crm_user or frappe.session.user
	if not crm_user or crm_user == "Guest":
		return None
	return frappe.db.get_value("CRM TripAI User Link", {"crm_user": crm_user, "enabled": 1}, "tripai_user_id")


def check_credits_for_sync(
	user_id: str,
	estimated_api_calls: int,
	estimated_poi_imports: int,
) -> dict[str, Any]:
	rates = get_billing_rates(user_id)
	amount = round(
		estimated_api_calls * rates["api_call"] + estimated_poi_imports * rates["poi_import"],
		2,
	)
	if amount <= 0:
		return {"sufficient": True, "required": 0, "balance": None}

	result = delegated_credits_check(user_id, amount)
	return {
		"sufficient": bool(result.get("available", result.get("sufficient"))),
		"required": amount,
		"balance": result.get("currentBalance", result.get("balance")),
	}


def consume_api_call(user_id: str, job_name: str, metadata: dict | None = None) -> None:
	if not should_bill_for_sync():
		return

	rates = get_billing_rates(user_id)
	amount = rates["api_call"]
	if amount <= 0:
		return

	delegated_credits_consume(
		user_id,
		amount,
		feature_key="amap_api_call",
		description=_("Amap API call for POI sync job {0}").format(job_name),
		metadata={"job_name": job_name, **(metadata or {})},
	)
	_increment_daily_usage(job_name, api_calls=1)


def consume_poi_import(user_id: str, job_name: str, poi_count: int = 1) -> None:
	if not should_bill_for_sync():
		return

	rates = get_billing_rates(user_id)
	amount = round(rates["poi_import"] * poi_count, 2)
	if amount <= 0:
		return

	delegated_credits_consume(
		user_id,
		amount,
		feature_key="poi_lead_import",
		description=_("POI lead import for job {0}").format(job_name),
		metadata={"job_name": job_name, "poi_count": poi_count},
	)
	_increment_daily_usage(job_name, poi_imports=poi_count)


def _increment_daily_usage(job_name: str, api_calls: int = 0, poi_imports: int = 0) -> None:
	if not frappe.db.exists("CRM POI Sync Job", job_name):
		return

	current = frappe.db.get_value("CRM POI Sync Job", job_name, "daily_usage") or 0
	# daily_usage stores cumulative credits consumed for the job run
	rates = get_billing_rates()
	added = api_calls * rates["api_call"] + poi_imports * rates["poi_import"]
	frappe.db.set_value("CRM POI Sync Job", job_name, "daily_usage", round(float(current) + added, 4))


class InsufficientCreditsError(Exception):
	def __init__(self, required: float, balance: float | None = None):
		self.required = required
		self.balance = balance
		super().__init__(_("Insufficient TripAI credits"))
