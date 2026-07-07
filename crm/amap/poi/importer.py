"""Import Amap POI records into CRM POI Record and CRM Lead."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import now_datetime

from crm.amap.poi.normalize import (
	get_primary_phone,
	has_valid_phone,
	normalize_phone,
	parse_phone_rows,
	parse_photo_rows,
)


class POIImporter:
	def __init__(self, sync_job, settings, tripai_user_id: str | None = None):
		self.sync_job = sync_job
		self.settings = settings
		self.tripai_user_id = tripai_user_id
		self.import_only_with_phone = bool(
			sync_job.import_only_with_phone or settings.import_only_with_phone
		)
		self.stats = {
			"total_fetched": 0,
			"with_phone_count": 0,
			"leads_created": 0,
			"leads_skipped": 0,
		}

	def process_pois(self, pois: list[dict[str, Any]]):
		seen_ids: set[str] = set()
		for poi in pois:
			poi_id = poi.get("id")
			if not poi_id or poi_id in seen_ids:
				continue
			seen_ids.add(poi_id)
			self._process_single_poi(poi)

	def _process_single_poi(self, poi: dict[str, Any]):
		self.stats["total_fetched"] += 1
		tel = poi.get("tel") or ""
		phones = normalize_phone(tel)
		primary_phone = get_primary_phone(tel)
		valid_phone = has_valid_phone(tel)

		if valid_phone:
			self.stats["with_phone_count"] += 1

		poi_record_name = upsert_poi_record(
			poi,
			sync_job=self.sync_job.name,
			job_owner=self.sync_job.job_owner,
			agent_tenant_id=getattr(self.sync_job, "agent_tenant_id", None),
			phones=phones,
			primary_phone=primary_phone,
			valid_phone=valid_phone,
		)

		if self.import_only_with_phone and not valid_phone:
			self.stats["leads_skipped"] += 1
			self._maybe_flush_stats()
			return

		duplicate_phone_lead = (
			frappe.db.get_value("CRM Lead", {"mobile_no": primary_phone}) if primary_phone else None
		)
		lead_name = create_or_update_lead(
			poi,
			sync_job=self.sync_job,
			settings=self.settings,
			phones=phones,
			primary_phone=primary_phone,
			valid_phone=valid_phone,
		)

		if lead_name:
			frappe.db.set_value("CRM POI Record", poi_record_name, "lead", lead_name)
			if duplicate_phone_lead and duplicate_phone_lead == lead_name:
				self.stats["leads_skipped"] += 1
				frappe.db.set_value("CRM POI Record", poi_record_name, "skip_reason", "duplicate_phone")
			else:
				self.stats["leads_created"] += 1
			if valid_phone and not duplicate_phone_lead:
				self._bill_poi_import()
		else:
			self.stats["leads_skipped"] += 1

		self._maybe_flush_stats()

	def _maybe_flush_stats(self) -> None:
		if self.stats["total_fetched"] % 10 != 0:
			return
		self.sync_job.update_stats(
			total_fetched=self.stats["total_fetched"],
			with_phone_count=self.stats["with_phone_count"],
			leads_created=self.stats["leads_created"],
			leads_skipped=self.stats["leads_skipped"],
		)

	def _bill_poi_import(self) -> None:
		if not self.tripai_user_id:
			return
		from crm.integrations.tripai.billing import consume_poi_import, should_bill_for_sync

		if not should_bill_for_sync(self.settings):
			return

		consume_poi_import(self.tripai_user_id, self.sync_job.name, poi_count=1)


def upsert_poi_record(
	poi: dict[str, Any],
	sync_job: str,
	job_owner: str,
	phones: list[str],
	primary_phone: str | None,
	valid_phone: bool,
	agent_tenant_id: str | None = None,
) -> str:
	amap_poi_id = poi.get("id")
	existing = frappe.db.exists("CRM POI Record", amap_poi_id)
	location = _format_geolocation(poi.get("location"))
	phone_rows = parse_phone_rows(poi.get("tel"))
	photo_rows = parse_photo_rows(poi.get("photos"))
	biz_ext = poi.get("biz_ext") if isinstance(poi.get("biz_ext"), dict) else {}
	all_phones = "\n".join(
		row.get("normalized_value") or row.get("raw_value") or "" for row in phone_rows
	)

	doc_data = {
		"doctype": "CRM POI Record",
		"amap_poi_id": amap_poi_id,
		"parent_poi_id": poi.get("parent") or "",
		"name1": poi.get("name") or amap_poi_id,
		"tel": poi.get("tel") or "",
		"tel_normalized": primary_phone or (phones[0] if phones else ""),
		"all_phones": all_phones,
		"has_valid_phone": 1 if valid_phone else 0,
		"website": poi.get("website") or "",
		"email": poi.get("email") or "",
		"postcode": poi.get("postcode") or "",
		"address": poi.get("address") or "",
		"location": location,
		"poi_type": poi.get("type") or "",
		"poi_typecode": poi.get("typecode") or "",
		"biz_type": poi.get("biz_type") or "",
		"business_area": poi.get("business_area") or "",
		"tag": poi.get("tag") or "",
		"rating": poi.get("rating") or biz_ext.get("rating") or "",
		"cost": poi.get("cost") or biz_ext.get("cost") or "",
		"alias": poi.get("alias") or "",
		"province": poi.get("pname") or poi.get("province") or "",
		"pcode": poi.get("pcode") or "",
		"city": poi.get("cityname") or poi.get("city") or "",
		"citycode": poi.get("citycode") or "",
		"district": poi.get("adname") or poi.get("district") or "",
		"adcode": poi.get("adcode") or "",
		"primary_photo_url": photo_rows[0]["url"] if photo_rows else "",
		"photo_count": len(photo_rows),
		"sync_job": sync_job,
		"job_owner": job_owner,
		"agent_tenant_id": agent_tenant_id,
		"last_synced_at": now_datetime(),
		"source_api_version": poi.get("_source_api_version") or "v3",
		"sync_action": "Updated" if existing else "Inserted",
		"skip_reason": "",
		"is_truncated_source": 1 if poi.get("_truncated") else 0,
		"raw_json": json.dumps(poi, ensure_ascii=False),
		"phones": phone_rows,
		"photos": photo_rows,
	}

	if existing:
		doc = frappe.get_doc("CRM POI Record", existing)
		doc.update(doc_data)
		doc.set("phones", [])
		for row in phone_rows:
			doc.append("phones", row)
		doc.set("photos", [])
		for row in photo_rows:
			doc.append("photos", row)
		doc.save(ignore_permissions=True)
		return doc.name

	doc = frappe.get_doc(doc_data)
	doc.insert(ignore_permissions=True)
	return doc.name


def create_or_update_lead(
	poi: dict[str, Any],
	sync_job,
	settings,
	phones: list[str],
	primary_phone: str | None,
	valid_phone: bool,
) -> str | None:
	amap_poi_id = poi.get("id")
	if not amap_poi_id:
		return None

	existing_lead = frappe.db.get_value("CRM Lead", {"amap_poi_id": amap_poi_id})
	if existing_lead:
		update_existing_lead_from_poi(existing_lead, poi, phones, primary_phone, valid_phone)
		return existing_lead

	if primary_phone and frappe.db.exists("CRM Lead", {"mobile_no": primary_phone}):
		return frappe.db.get_value("CRM Lead", {"mobile_no": primary_phone})

	lead_owner = sync_job.assign_to or settings.default_lead_owner or sync_job.job_owner
	lead_source = sync_job.lead_source or "高德地图"
	organization = poi.get("name") or amap_poi_id
	location = _format_geolocation(poi.get("location"))

	status = "新线索"
	if valid_phone and frappe.db.exists("CRM Lead Status", "待拨打"):
		status = "待拨打"
	elif not frappe.db.exists("CRM Lead Status", "新线索"):
		status = None

	lead_data = {
		"doctype": "CRM Lead",
		"organization": organization,
		"first_name": organization,
		"lead_name": organization,
		"mobile_no": primary_phone or "",
		"phone": phones[1] if len(phones) > 1 else "",
		"source": lead_source,
		"lead_owner": lead_owner,
		"status": status,
		"amap_poi_id": amap_poi_id,
		"tripai_agent_tenant_id": getattr(sync_job, "agent_tenant_id", None),
		"poi_address": poi.get("address") or "",
		"poi_location": location,
		"poi_type": poi.get("type") or "",
		"poi_typecode": poi.get("typecode") or "",
		"district": poi.get("adname") or poi.get("district") or "",
		"has_valid_phone": 1 if valid_phone else 0,
	}

	if settings.default_product:
		lead_data["recommended_product"] = settings.default_product

	doc = frappe.get_doc(lead_data)
	doc.insert(ignore_permissions=True)
	return doc.name


def update_existing_lead_from_poi(
	lead_name: str,
	poi: dict[str, Any],
	phones: list[str],
	primary_phone: str | None,
	valid_phone: bool,
) -> None:
	try:
		frappe.db.set_value(
			"CRM Lead",
			lead_name,
			{
				"poi_address": poi.get("address") or "",
				"poi_location": _format_geolocation(poi.get("location")),
				"poi_type": poi.get("type") or "",
				"poi_typecode": poi.get("typecode") or "",
				"district": poi.get("adname") or poi.get("district") or "",
				"has_valid_phone": 1 if valid_phone else 0,
				"mobile_no": primary_phone or "",
				"phone": phones[1] if len(phones) > 1 else "",
			},
		)
	except Exception:
		return


def promote_poi_to_lead(poi_record_name: str) -> str:
	poi_record = frappe.get_doc("CRM POI Record", poi_record_name)
	if poi_record.lead:
		return poi_record.lead

	settings = frappe.get_single("CRM Amap Settings")
	sync_job = frappe.get_doc("CRM POI Sync Job", poi_record.sync_job)
	poi = json.loads(poi_record.raw_json or "{}")
	poi.setdefault("id", poi_record.amap_poi_id)
	poi.setdefault("name", poi_record.name1)
	poi.setdefault("tel", poi_record.tel)
	poi.setdefault("address", poi_record.address)
	poi.setdefault("type", poi_record.poi_type)
	poi.setdefault("typecode", poi_record.poi_typecode)
	poi.setdefault("adname", poi_record.district)
	poi.setdefault("cityname", poi_record.city)

	phones = normalize_phone(poi_record.tel)
	primary_phone = get_primary_phone(poi_record.tel)
	valid_phone = bool(poi_record.has_valid_phone)

	lead_name = create_or_update_lead(
		poi,
		sync_job=sync_job,
		settings=settings,
		phones=phones,
		primary_phone=primary_phone,
		valid_phone=valid_phone,
	)
	if lead_name:
		frappe.db.set_value("CRM POI Record", poi_record_name, "lead", lead_name)
	return lead_name or ""


def _format_geolocation(location: str | None) -> str | None:
	if not location or "," not in location:
		return None
	lng_str, lat_str = location.split(",", 1)
	try:
		lng = float(lng_str.strip())
		lat = float(lat_str.strip())
	except ValueError:
		return None
	return json.dumps(
		{
			"type": "FeatureCollection",
			"features": [
				{
					"type": "Feature",
					"properties": {},
					"geometry": {"type": "Point", "coordinates": [lng, lat]},
				}
			],
		}
	)
