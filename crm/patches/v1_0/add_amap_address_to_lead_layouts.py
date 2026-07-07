import json

import frappe
from frappe.utils import parse_json

from crm.fcrm.doctype.crm_view_settings.crm_view_settings import normalize_list_columns

LOCATION_SECTION = {
	"label": "Location",
	"name": "location_section",
	"opened": True,
	"columns": [{"name": "column_loc", "fields": ["poi_address", "district"]}],
}

AMAP_VIEW_UPDATES = {
	"高德-待拨打": [
		"lead_name",
		"mobile_no",
		"organization",
		"poi_address",
		"recommended_product",
		"status",
		"lead_owner",
	],
	"高德-有意向": [
		"lead_name",
		"mobile_no",
		"organization",
		"poi_address",
		"recommended_product",
		"status",
		"lead_owner",
	],
	"高德-今日已联系": [
		"lead_name",
		"mobile_no",
		"organization",
		"poi_address",
		"recommended_product",
		"lead_owner",
	],
	"高德-新线索": [
		"lead_name",
		"mobile_no",
		"organization",
		"status",
		"poi_type",
		"poi_address",
		"lead_owner",
	],
}


def execute():
	_add_location_section_to_side_panel()
	_add_poi_address_to_data_fields()
	_update_amap_list_views()


def _layout_has_field(layout, fieldname: str) -> bool:
	for section in layout:
		for column in section.get("columns") or []:
			if fieldname in (column.get("fields") or []):
				return True
	return False


def _add_location_section_to_side_panel():
	name = {"dt": "CRM Lead", "type": "Side Panel"}
	if not frappe.db.exists("CRM Fields Layout", name):
		return

	doc = frappe.get_doc("CRM Fields Layout", name)
	layout = parse_json(doc.layout or "[]")
	if _layout_has_field(layout, "poi_address"):
		return

	layout.append(LOCATION_SECTION)
	doc.layout = json.dumps(layout)
	doc.save(ignore_permissions=True)


def _add_poi_address_to_data_fields():
	name = {"dt": "CRM Lead", "type": "Data Fields"}
	if not frappe.db.exists("CRM Fields Layout", name):
		return

	doc = frappe.get_doc("CRM Fields Layout", name)
	layout = parse_json(doc.layout or "[]")
	if _layout_has_field(layout, "poi_address"):
		return

	for section in layout:
		columns = section.get("columns") or []
		if not columns:
			continue
		fields = columns[0].setdefault("fields", [])
		if "poi_address" not in fields:
			fields.append("poi_address")
		if len(columns) > 1:
			detail_fields = columns[1].setdefault("fields", [])
			if "district" not in detail_fields:
				detail_fields.append("district")
		break

	doc.layout = json.dumps(layout)
	doc.save(ignore_permissions=True)


def _update_amap_list_views():
	for label, fieldnames in AMAP_VIEW_UPDATES.items():
		view_name = frappe.db.exists("CRM View Settings", {"label": label, "dt": "CRM Lead"})
		if not view_name:
			continue
		columns = json.dumps(normalize_list_columns(fieldnames, "CRM Lead"))
		frappe.db.set_value(
			"CRM View Settings",
			view_name,
			"columns",
			columns,
			update_modified=False,
		)
