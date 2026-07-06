"""Amap Web API client with mock mode and key rotation."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any

import requests

import frappe
from frappe import _

from crm.amap.poi.errors import format_amap_error
from crm.amap.poi.mock_data import generate_mock_pois

AMAP_TEXT_URL = "https://restapi.amap.com/v3/place/text"
AMAP_POLYGON_URL = "https://restapi.amap.com/v3/place/polygon"
AMAP_DISTRICT_URL = "https://restapi.amap.com/v3/config/district"
REQUEST_TIMEOUT = 10
MAX_RETRIES = 3
RETRY_DELAYS = [1, 2, 4]
MIN_REQUEST_INTERVAL = 0.34


@dataclass
class APIResult:
	success: bool = False
	data: list[dict[str, Any]] = field(default_factory=list)
	count: int = 0
	error_message: str = ""
	status: str = ""
	info: str = ""


class AmapClient:
	def __init__(
		self,
		api_keys: list[str] | None = None,
		request_interval: float = 0.35,
		use_mock: bool = False,
		on_api_call=None,
	):
		self.api_keys = api_keys or []
		self.request_interval = max(request_interval, MIN_REQUEST_INTERVAL)
		self.use_mock = use_mock or not self.api_keys
		self.on_api_call = on_api_call
		self._current_key_index = 0
		self._last_request_time = 0.0
		self._key_last_request: dict[str, float] = {key: 0.0 for key in self.api_keys}

	def test_connection(self) -> dict[str, Any]:
		if self.use_mock:
			return {"success": True, "message": _("Mock API mode enabled")}

		api_key = self._get_current_key()
		if not api_key:
			return {"success": False, "message": _("No API keys configured. Please add and save one first.")}

		# Use district API — same Web服务 key type as POI search, lighter payload
		params = {
			"key": api_key,
			"keywords": "110000",
			"subdistrict": 0,
			"extensions": "base",
		}
		data, error = self._make_request(AMAP_DISTRICT_URL, params, api_key)
		if error:
			return {"success": False, "message": error}

		if data.get("status") == "1":
			return {"success": True, "message": _("Connection successful, Web服务 Key is valid")}

		info = data.get("info", "")
		return {"success": False, "message": format_amap_error(info), "code": info}

	def search_text(
		self,
		keywords: str = "",
		city: str = "",
		types: str = "",
		limit: int = 10,
		page: int = 1,
	) -> APIResult:
		if self.use_mock:
			data, count = generate_mock_pois(
				keywords=keywords,
				city=city,
				types=types,
				limit=limit,
				page=page,
			)
			return APIResult(success=True, data=data, count=count)

		params = {
			"keywords": keywords,
			"city": city,
			"offset": min(limit, 25),
			"page": page,
			"extensions": "all",
		}
		if types:
			params["types"] = types
		return self._search(AMAP_TEXT_URL, params)

	def search_polygon(
		self,
		polygon: str,
		keywords: str = "",
		types: str = "",
		page_size: int = 25,
		page_num: int = 1,
	) -> APIResult:
		if self.use_mock:
			city = keywords or "杭州"
			data, count = generate_mock_pois(
				keywords=keywords,
				city=city,
				types=types,
				limit=page_size,
				page=page_num,
			)
			if page_num > 1 and page_num > (count // page_size) + 1:
				data = []
			return APIResult(success=True, data=data, count=count)

		params = {
			"polygon": polygon,
			"offset": min(page_size, 25),
			"page": page_num,
			"extensions": "all",
		}
		if keywords:
			params["keywords"] = keywords
		if types:
			params["types"] = types
		return self._search(AMAP_POLYGON_URL, params)

	def get_district_bbox(self, adcode: str) -> tuple[float, float, float, float] | None:
		if self.use_mock:
			return (120.0, 30.0, 120.2, 30.2)

		api_key = self._get_current_key()
		if not api_key:
			return None

		params = {
			"key": api_key,
			"keywords": adcode,
			"subdistrict": 0,
			"extensions": "all",
		}
		data, error = self._make_request(AMAP_DISTRICT_URL, params, api_key)
		if error or not data or data.get("status") != "1":
			return None

		districts = data.get("districts") or []
		if not districts:
			return None

		from crm.amap.poi.quadtree import bbox_from_polyline

		polyline = districts[0].get("polyline")
		if not polyline:
			return None

		bounds = bbox_from_polyline(polyline)
		if not bounds:
			return None
		return (bounds.min_lng, bounds.min_lat, bounds.max_lng, bounds.max_lat)

	def _search(self, url: str, params: dict[str, Any]) -> APIResult:
		api_key = self._get_current_key()
		if not api_key:
			return APIResult(success=False, error_message=_("No API keys configured"))

		params = {**params, "key": api_key}
		data, error = self._make_request(url, params, api_key)
		if error:
			return APIResult(success=False, error_message=error)

		status = data.get("status", "")
		info = data.get("info", "")
		if status != "1":
			if info in {
				"DAILY_QUERY_OVER_LIMIT",
				"USER_DAILY_QUERY_OVER_LIMIT",
				"ACCESS_TOO_FREQUENT",
				"CUQPS_HAS_EXCEEDED_THE_LIMIT",
			}:
				self._rotate_key()
				return self._search(url, {k: v for k, v in params.items() if k != "key"})
			return APIResult(success=False, error_message=format_amap_error(info), status=status, info=info)

		pois = data.get("pois") or []
		count = int(data.get("count") or len(pois))
		return APIResult(success=True, data=pois, count=count, status=status, info=info)

	def _get_current_key(self) -> str | None:
		if not self.api_keys:
			return None
		return self.api_keys[self._current_key_index % len(self.api_keys)]

	def _rotate_key(self):
		if len(self.api_keys) > 1:
			self._current_key_index = (self._current_key_index + 1) % len(self.api_keys)

	def _wait_for_interval(self, key: str | None = None):
		current_time = time.time()
		elapsed = current_time - self._last_request_time
		if elapsed < self.request_interval:
			time.sleep(self.request_interval - elapsed)

		if key and key in self._key_last_request:
			key_elapsed = current_time - self._key_last_request[key]
			if key_elapsed < MIN_REQUEST_INTERVAL:
				time.sleep(MIN_REQUEST_INTERVAL - key_elapsed)
			self._key_last_request[key] = time.time()

		self._last_request_time = time.time()

	def _make_request(
		self, url: str, params: dict[str, Any], key: str | None = None
	) -> tuple[dict[str, Any] | None, str | None]:
		for attempt in range(MAX_RETRIES):
			try:
				self._wait_for_interval(key)
				response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
				response.raise_for_status()
				if not self.use_mock and self.on_api_call:
					self.on_api_call()
				return response.json(), None
			except requests.exceptions.Timeout:
				if attempt < MAX_RETRIES - 1:
					time.sleep(RETRY_DELAYS[attempt])
			except requests.exceptions.RequestException as exc:
				try:
					import frappe

					frappe.log_error(title="Amap API request failed", message=str(exc))
				except Exception:
					pass
				if attempt < MAX_RETRIES - 1:
					time.sleep(RETRY_DELAYS[attempt])
			except json.JSONDecodeError as exc:
				return None, _("Invalid JSON response: {0}").format(exc)

		return None, _("Request failed after {0} retries").format(MAX_RETRIES)


def build_client_from_settings(settings=None, tripai_user_id: str | None = None, job_name: str | None = None) -> AmapClient:
	import frappe

	if settings is None:
		settings = frappe.get_single("CRM Amap Settings")

	api_keys = []
	use_mock = bool(settings.use_mock_api)
	on_api_call = None

	from crm.integrations.tripai.billing import should_bill_for_sync

	billing = should_bill_for_sync(settings) if not use_mock else False

	if billing:
		from crm.integrations.tripai.billing import (
			RuntimeConfigError,
			consume_api_call,
			get_runtime_amap_keys,
		)

		api_keys = get_runtime_amap_keys(required=True)

		if tripai_user_id and job_name:

			def _bill_api_call():
				consume_api_call(tripai_user_id, job_name)

			on_api_call = _bill_api_call
	elif not use_mock:
		try:
			from crm.integrations.tripai.billing import get_runtime_amap_keys, should_bill_for_sync

			if should_bill_for_sync(settings):
				api_keys = get_runtime_amap_keys()
		except Exception:
			pass

	if not api_keys:
		for row in settings.api_keys or []:
			key = row.get_password("api_key")
			if key:
				api_keys.append(key)

	if billing and not api_keys:
		from crm.integrations.tripai.billing import RuntimeConfigError

		raise RuntimeConfigError(_("Amap API keys are not available from TripAI"))

	use_mock = use_mock or not api_keys
	return AmapClient(
		api_keys=api_keys,
		request_interval=settings.request_interval or 0.35,
		use_mock=use_mock,
		on_api_call=on_api_call,
	)
