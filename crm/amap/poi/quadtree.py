"""Quadtree splitting for Amap POI polygon search."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable

import frappe
from frappe import _

logger = logging.getLogger(__name__)

DEFAULT_THRESHOLD = 180
MIN_GRID_SPAN = 0.005
MAX_DEPTH = 20


class AmapSearchError(Exception):
	def __init__(self, message: str, code: str = ""):
		super().__init__(message)
		self.code = code


@dataclass
class BoundingBox:
	min_lng: float
	min_lat: float
	max_lng: float
	max_lat: float

	@property
	def width(self) -> float:
		return self.max_lng - self.min_lng

	@property
	def height(self) -> float:
		return self.max_lat - self.min_lat

	def to_polygon(self) -> str:
		return f"{self.min_lng},{self.min_lat}|{self.max_lng},{self.max_lat}"

	def split(self) -> list["BoundingBox"]:
		mid_lng = (self.min_lng + self.max_lng) / 2
		mid_lat = (self.min_lat + self.max_lat) / 2
		return [
			BoundingBox(self.min_lng, self.min_lat, mid_lng, mid_lat),
			BoundingBox(mid_lng, self.min_lat, self.max_lng, mid_lat),
			BoundingBox(self.min_lng, mid_lat, mid_lng, self.max_lat),
			BoundingBox(mid_lng, mid_lat, self.max_lng, self.max_lat),
		]


class QuadTreeSplitter:
	def __init__(
		self,
		api_client,
		poi_threshold: int = DEFAULT_THRESHOLD,
		min_grid_span: float = MIN_GRID_SPAN,
		max_depth: int = MAX_DEPTH,
	):
		self.api_client = api_client
		self.poi_threshold = poi_threshold
		self.min_grid_span = min_grid_span
		self.max_depth = max_depth
		self._cancelled = False

	def cancel(self):
		self._cancelled = True

	def fetch_pois_in_bounds(
		self,
		bounds: BoundingBox,
		keywords: str = "",
		types: str = "",
	) -> tuple[list[dict[str, Any]], bool, int]:
		polygon = bounds.to_polygon()

		result = self.api_client.search_polygon(
			polygon=polygon,
			keywords=keywords,
			types=types,
			page_size=25,
			page_num=1,
		)
		if not result.success:
			raise AmapSearchError(result.error_message or _("Amap polygon search failed"), result.info or "")
		if not result.data:
			return [], False, 0

		reported_count = result.count or len(result.data)
		if reported_count > self.poi_threshold:
			return result.data, True, reported_count

		all_pois: list[dict[str, Any]] = list(result.data)
		page = 2
		while page <= 8:
			if self._cancelled:
				break

			result = self.api_client.search_polygon(
				polygon=polygon,
				keywords=keywords,
				types=types,
				page_size=25,
				page_num=page,
			)
			if not result.success:
				raise AmapSearchError(result.error_message or _("Amap polygon search failed"), result.info or "")
			if not result.data:
				break

			all_pois.extend(result.data)
			if len(result.data) < 25:
				break
			page += 1

		return all_pois, False, reported_count

	def fetch_available_pois_in_bounds(
		self,
		bounds: BoundingBox,
		keywords: str = "",
		types: str = "",
	) -> list[dict[str, Any]]:
		polygon = bounds.to_polygon()
		all_pois: list[dict[str, Any]] = []
		page = 1
		while page <= 8:
			if self._cancelled:
				break

			result = self.api_client.search_polygon(
				polygon=polygon,
				keywords=keywords,
				types=types,
				page_size=25,
				page_num=page,
			)
			if not result.success:
				raise AmapSearchError(result.error_message or _("Amap polygon search failed"), result.info or "")
			if not result.data:
				break

			all_pois.extend(result.data)
			if len(result.data) < 25:
				break
			page += 1

		return all_pois

	def quadtree_split(
		self,
		bounds: BoundingBox,
		keywords: str = "",
		types: str = "",
		current_depth: int = 0,
		on_log: Callable[[str], None] | None = None,
	) -> list[dict[str, Any]]:
		if self._cancelled:
			return []

		pois, need_split, reported_count = self.fetch_pois_in_bounds(bounds, keywords, types)
		if not need_split:
			return pois

		if bounds.width < self.min_grid_span or bounds.height < self.min_grid_span:
			if on_log:
				on_log(_("Grid reached minimum span, keeping available POI data"))
			return self.fetch_available_pois_in_bounds(bounds, keywords, types) or pois

		if current_depth >= self.max_depth:
			if on_log:
				on_log(_("Reached max recursion depth, keeping available POI data"))
			return self.fetch_available_pois_in_bounds(bounds, keywords, types) or pois

		all_pois: list[dict[str, Any]] = []
		if on_log:
			on_log(
				_("Grid reported {0} POIs, splitting for better coverage").format(reported_count)
			)
		for sub_bounds in bounds.split():
			if self._cancelled:
				break
			all_pois.extend(
				self.quadtree_split(
					sub_bounds,
					keywords=keywords,
					types=types,
					current_depth=current_depth + 1,
					on_log=on_log,
				)
			)
		return all_pois


def bbox_from_polyline(polyline: str) -> BoundingBox | None:
	try:
		if not polyline or not polyline.strip():
			return None

		coords: list[tuple[float, float]] = []
		for polygon in polyline.split("|"):
			for point_str in polygon.split(";"):
				point_str = point_str.strip()
				if not point_str or "," not in point_str:
					continue
				lng_str, lat_str = point_str.split(",", 1)
				coords.append((float(lng_str.strip()), float(lat_str.strip())))

		if not coords:
			return None

		lngs = [coord[0] for coord in coords]
		lats = [coord[1] for coord in coords]
		return BoundingBox(min(lngs), min(lats), max(lngs), max(lats))
	except Exception as exc:
		logger.error("Failed to parse polyline: %s", exc)
		return None


def bbox_from_string(bbox: str) -> BoundingBox | None:
	try:
		parts = [float(part.strip()) for part in bbox.split(",")]
		if len(parts) != 4:
			return None
		return BoundingBox(parts[0], parts[1], parts[2], parts[3])
	except ValueError:
		return None
