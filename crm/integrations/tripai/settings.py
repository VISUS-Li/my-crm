# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import annotations

import os
from typing import Any

import frappe
import requests


class TripAIConfigError(Exception):
	pass


class TripAIAPIError(Exception):
	def __init__(self, message: str, status_code: int | None = None, payload: dict | None = None):
		super().__init__(message)
		self.status_code = status_code
		self.payload = payload or {}


def _conf_value(key: str, default: str = "") -> str:
	try:
		value = frappe.conf.get(key)
	except Exception:
		return default
	return (value or default).strip() if isinstance(value, str) else default


def get_tripai_settings() -> dict[str, str]:
	"""Resolve TripAI connection settings from DocType, site config, and env."""
	enabled = False
	base_url = os.environ.get("TRIPAI_BASE_URL", "").strip() or _conf_value("tripai_base_url")
	project_key = os.environ.get("TRIPAI_PROJECT_KEY", "").strip() or _conf_value("tripai_project_key", "nextdevtpl")
	tool_key = os.environ.get("TRIPAI_TOOL_KEY", "").strip() or _conf_value("tripai_tool_key", "my-crm")
	runtime_token = os.environ.get("TRIPAI_RUNTIME_TOKEN", "")
	default_redirect_path = "/crm"
	require_license = True

	if frappe.db.exists("DocType", "CRM TripAI Settings"):
		doc = frappe.get_single("CRM TripAI Settings")
		enabled = bool(doc.enabled)
		base_url = (doc.base_url or "").strip() or base_url
		project_key = (doc.project_key or "").strip() or project_key
		tool_key = (doc.tool_key or "").strip() or tool_key
		stored_token = doc.get_password("runtime_token")
		if stored_token:
			runtime_token = stored_token
		default_redirect_path = doc.default_redirect_path or default_redirect_path
		require_license = bool(getattr(doc, "require_license", 1))

	if not base_url:
		raise TripAIConfigError("TripAI base URL is not configured")

	return {
		"enabled": enabled,
		"base_url": base_url.rstrip("/"),
		"project_key": project_key,
		"tool_key": tool_key,
		"runtime_token": runtime_token,
		"default_redirect_path": default_redirect_path,
		"require_license": require_license,
	}
