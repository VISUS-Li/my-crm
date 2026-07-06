"""Import Amap POI records into CRM POI Record and CRM Lead."""

from __future__ import annotations

import json
from typing import Any

import frappe

from crm.amap.poi.normalize import get_primary_phone, has_valid_phone, normalize_phone


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
			return

		lead_name = create_or_update_lead(
			poi,
			sync_job=self.sync_job,
			settings=self.settings,
			phones=phones,
			primary_phone=primary_phone,
			valid_phone=valid_phone,
		)

		if lead_name:
			self.stats["leads_created"] += 1
			frappe.db.set_value("CRM POI Record", poi_record_name, "lead", lead_name)
			if valid_phone:
				self._bill_poi_import()
		else:
			self.stats["leads_skipped"] += 1

	def _bill_poi_import(self) -> None:
		if self.settings.use_mock_api or not self.tripai_user_id:
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

	doc_data = {
		"doctype": "CRM POI Record",
		"amap_poi_id": amap_poi_id,
		"name1": poi.get("name") or amap_poi_id,
		"tel": poi.get("tel") or "",
		"tel_normalized": primary_phone or (phones[0] if phones else ""),
		"has_valid_phone": 1 if valid_phone else 0,
		"address": poi.get("address") or "",
		"location": location,
		"poi_type": poi.get("type") or "",
		"poi_typecode": poi.get("typecode") or "",
		"province": poi.get("pname") or poi.get("province") or "",
		"city": poi.get("cityname") or poi.get("city") or "",
		"district": poi.get("adname") or poi.get("district") or "",
		"sync_job": sync_job,
		"job_owner": job_owner,
		"agent_tenant_id": agent_tenant_id,
		"raw_json": json.dumps(poi, ensure_ascii=False),
	}

	if existing:
		doc = frappe.get_doc("CRM POI Record", existing)
		doc.update(doc_data)
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
		return existing_lead

	if primary_phone and frappe.db.exists("CRM Lead", {"mobile_no": primary_phone}):
		return None

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
