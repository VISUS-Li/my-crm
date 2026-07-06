# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import annotations

from typing import Any

import requests

from crm.integrations.tripai.settings import TripAIAPIError, TripAIConfigError, get_tripai_settings


def _request(
	method: str,
	path: str,
	*,
	json: dict | None = None,
	timeout: int = 30,
) -> dict[str, Any]:
	settings = get_tripai_settings()
	if not settings["runtime_token"]:
		raise TripAIConfigError("TripAI runtime token is not configured")

	url = f"{settings['base_url']}{path}"
	headers = {
		"Authorization": f"Bearer {settings['runtime_token']}",
		"Content-Type": "application/json",
	}

	response = requests.request(method, url, json=json, headers=headers, timeout=timeout)
	try:
		payload = response.json()
	except ValueError as exc:
		raise TripAIAPIError(
			f"TripAI returned non-JSON response ({response.status_code})",
			status_code=response.status_code,
		) from exc

	if not response.ok or not payload.get("success"):
		error = payload.get("error") or f"TripAI API error ({response.status_code})"
		raise TripAIAPIError(str(error), status_code=response.status_code, payload=payload)

	return payload


def exchange_launch_ticket(ticket: str, project_key: str | None = None) -> dict[str, Any]:
	settings = get_tripai_settings()
	return _request(
		"POST",
		"/api/platform/tools/session/exchange",
		json={
			"projectKey": project_key or settings["project_key"],
			"tool": settings["tool_key"],
			"ticket": ticket,
		},
	)


def fetch_runtime_config(user_id: str | None = None) -> dict[str, Any]:
	settings = get_tripai_settings()
	payload: dict[str, Any] = {
		"projectKey": settings["project_key"],
		"tool": settings["tool_key"],
	}
	if user_id:
		payload["userId"] = user_id
	return _request("POST", "/api/platform/tool-config/runtime", json=payload)


def delegated_credits_check(user_id: str, amount: float) -> dict[str, Any]:
	settings = get_tripai_settings()
	return _request(
		"POST",
		"/api/platform/credits/delegated/check",
		json={
			"projectKey": settings["project_key"],
			"tool": settings["tool_key"],
			"userId": user_id,
			"amount": amount,
		},
	)


def delegated_credits_consume(
	user_id: str,
	amount: float,
	*,
	feature_key: str,
	description: str,
	metadata: dict | None = None,
) -> dict[str, Any]:
	settings = get_tripai_settings()
	return _request(
		"POST",
		"/api/platform/credits/delegated/consume",
		json={
			"projectKey": settings["project_key"],
			"tool": settings["tool_key"],
			"userId": user_id,
			"amount": amount,
			"serviceName": f"{settings['tool_key']}:{feature_key}",
			"description": description,
			"metadata": metadata or {},
		},
	)


def fetch_delegated_entitlement(user_id: str) -> dict[str, Any]:
	settings = get_tripai_settings()
	tool_key = settings["tool_key"]
	return _request(
		"POST",
		f"/api/platform/tools/{tool_key}/entitlement/delegated",
		json={
			"projectKey": settings["project_key"],
			"tool": tool_key,
			"userId": user_id,
		},
	)


def activate_delegated_license(
	user_id: str,
	license_key: str,
	device_id: str,
	*,
	device_label: str | None = None,
) -> dict[str, Any]:
	settings = get_tripai_settings()
	tool_key = settings["tool_key"]
	payload: dict[str, Any] = {
		"projectKey": settings["project_key"],
		"tool": tool_key,
		"userId": user_id,
		"licenseKey": license_key,
		"deviceId": device_id,
	}
	if device_label:
		payload["deviceLabel"] = device_label
	return _request(
		"POST",
		f"/api/platform/tools/{tool_key}/license/activate/delegated",
		json=payload,
	)
