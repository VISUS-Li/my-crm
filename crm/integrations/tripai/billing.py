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

RUNTIME_CONFIG_CACHE_KEY = "tripai:runtime_config"
RUNTIME_CONFIG_CACHE_TTL = 120


class InsufficientCreditsError(Exception):
	def __init__(self, required: float, balance: float | None = None):
		self.required = required
		self.balance = balance
		super().__init__(_("Insufficient TripAI credits"))


class RuntimeConfigError(Exception):
	"""TripAI runtime config or Amap keys unavailable in production mode."""


def is_billing_enabled() -> bool:
	try:
		settings = get_tripai_settings()
	except TripAIConfigError:
		return False
	return bool(settings["enabled"] and settings["runtime_token"])


def should_bill_for_sync(settings=None) -> bool:
	return is_billing_enabled()


def clear_runtime_config_cache() -> None:
	frappe.cache().delete_value(RUNTIME_CONFIG_CACHE_KEY)


def _get_runtime_payload(force_refresh: bool = False) -> dict[str, Any]:
	if not is_billing_enabled():
		raise RuntimeConfigError(_("TripAI billing is not configured"))

	cache = frappe.cache()
	if not force_refresh:
		cached = cache.get_value(RUNTIME_CONFIG_CACHE_KEY)
		if cached:
			return cached

	try:
		payload = fetch_runtime_config()
	except TripAIAPIError as exc:
		raise RuntimeConfigError(str(exc)) from exc

	cache.set_value(RUNTIME_CONFIG_CACHE_KEY, payload, expires_in_sec=RUNTIME_CONFIG_CACHE_TTL)
	return payload


def get_runtime_amap_keys(user_id: str | None = None, *, required: bool = False) -> list[str]:
	_ = user_id  # reserved for future per-user key overrides
	if not is_billing_enabled():
		if required:
			raise RuntimeConfigError(_("TripAI integration is disabled"))
		return []

	payload = _get_runtime_payload()
	config = payload.get("config") or {}
	keys: list[str] = []
	for field in ("secret1", "secret2", "secret3"):
		value = config.get(field)
		if isinstance(value, str) and value.strip():
			keys.append(value.strip())

	if required and not keys:
		raise RuntimeConfigError(_("Amap API keys are not configured in TripAI tool-config"))
	return keys


def get_billing_rates() -> dict[str, float]:
	if not is_billing_enabled():
		return {"api_call": 0.0, "poi_import": 0.0}

	payload = _get_runtime_payload()
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


def resolve_billing_tripai_user_id(crm_user: str | None = None) -> str | None:
	"""TripAI user id used for license/credits — own link, else agent manager for employees."""
	crm_user = crm_user or frappe.session.user
	own = resolve_tripai_user_id(crm_user)
	if own:
		return own

	from crm.permissions.agent_tenant import resolve_agent_tenant_id

	tenant_id = resolve_agent_tenant_id(crm_user)
	if not tenant_id:
		return None

	links = frappe.get_all(
		"CRM TripAI User Link",
		filters={"agent_tenant_id": tenant_id, "enabled": 1},
		fields=["tripai_user_id", "crm_user"],
		order_by="modified desc",
	)
	for link in links:
		if "Sales Manager" in frappe.get_roles(link.crm_user):
			return link.tripai_user_id
	return links[0].tripai_user_id if links else None


def check_credits_for_sync(
	user_id: str,
	estimated_api_calls: int,
	estimated_poi_imports: int,
) -> dict[str, Any]:
	rates = get_billing_rates()
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


def _consume_or_raise(user_id: str, amount: float, **kwargs) -> None:
	try:
		delegated_credits_consume(user_id, amount, **kwargs)
	except TripAIAPIError as exc:
		message = str(exc).lower()
		if "insufficient" in message or "balance" in message or exc.status_code == 402:
			raise InsufficientCreditsError(amount) from exc
		raise


def consume_api_call(user_id: str, job_name: str, metadata: dict | None = None) -> None:
	if not should_bill_for_sync():
		return

	rates = get_billing_rates()
	amount = rates["api_call"]
	if amount <= 0:
		return

	_consume_or_raise(
		user_id,
		amount,
		feature_key="amap_api_call",
		description=_("Amap API call for POI sync job {0}").format(job_name),
		metadata={"job_name": job_name, **(metadata or {})},
	)
	_increment_daily_usage(job_name, api_calls=1, rates=rates)


def consume_poi_import(user_id: str, job_name: str, poi_count: int = 1) -> None:
	if not should_bill_for_sync():
		return

	rates = get_billing_rates()
	amount = round(rates["poi_import"] * poi_count, 2)
	if amount <= 0:
		return

	_consume_or_raise(
		user_id,
		amount,
		feature_key="poi_lead_import",
		description=_("POI lead import for job {0}").format(job_name),
		metadata={"job_name": job_name, "poi_count": poi_count},
	)
	_increment_daily_usage(job_name, poi_imports=poi_count, rates=rates)


def _increment_daily_usage(
	job_name: str,
	*,
	api_calls: int = 0,
	poi_imports: int = 0,
	rates: dict[str, float] | None = None,
) -> None:
	if not frappe.db.exists("CRM POI Sync Job", job_name):
		return

	if rates is None:
		rates = get_billing_rates()
	current = frappe.db.get_value("CRM POI Sync Job", job_name, "daily_usage") or 0
	added = api_calls * rates["api_call"] + poi_imports * rates["poi_import"]
	frappe.db.set_value("CRM POI Sync Job", job_name, "daily_usage", round(float(current) + added, 4))
