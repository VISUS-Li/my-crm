"""Lead media helpers — photos from profile image, POI sync, and attachments."""

from __future__ import annotations

import frappe
from frappe import _

_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg"}


def _is_image_filename(filename: str | None) -> bool:
	if not filename:
		return False
	lower = filename.lower()
	return any(lower.endswith(ext) for ext in _IMAGE_EXTENSIONS)


def _append_photo(photos: list[dict], url: str, title: str = "") -> None:
	if not url:
		return
	if any(photo.get("url") == url for photo in photos):
		return
	photos.append({"url": url, "title": title or ""})


def _photos_from_poi_record(amap_poi_id: str, photos: list[dict]) -> None:
	if not amap_poi_id or not frappe.db.exists("CRM POI Record", amap_poi_id):
		return

	poi = frappe.get_doc("CRM POI Record", amap_poi_id)
	for row in poi.photos or []:
		_append_photo(photos, row.url, row.title or "")
	if poi.primary_photo_url:
		_append_photo(photos, poi.primary_photo_url, _("Storefront"))


def _photos_from_attachments(lead_name: str, photos: list[dict]) -> None:
	files = frappe.get_all(
		"File",
		filters={
			"attached_to_doctype": "CRM Lead",
			"attached_to_name": lead_name,
			"is_folder": 0,
		},
		fields=["file_url", "file_name"],
		order_by="creation desc",
	)
	for file_doc in files:
		if _is_image_filename(file_doc.file_name):
			_append_photo(photos, file_doc.file_url, file_doc.file_name or "")


@frappe.whitelist()
def get_lead_photos(lead_name: str) -> list[dict]:
	frappe.has_permission("CRM Lead", "read", lead_name, throw=True)

	lead = frappe.get_doc("CRM Lead", lead_name)
	photos: list[dict] = []

	if lead.get("image"):
		_append_photo(photos, lead.image, _("Profile Image"))

	_photos_from_poi_record(lead.get("amap_poi_id"), photos)
	_photos_from_attachments(lead.name, photos)

	return photos
