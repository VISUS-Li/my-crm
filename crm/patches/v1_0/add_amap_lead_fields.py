import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	custom_fields = {
		"CRM Lead": [
			{
				"fieldname": "amap_poi_id",
				"fieldtype": "Data",
				"label": "Amap POI ID",
				"insert_after": "source",
				"unique": 1,
			},
			{
				"fieldname": "poi_address",
				"fieldtype": "Small Text",
				"label": "POI Address",
				"insert_after": "amap_poi_id",
			},
			{
				"fieldname": "poi_location",
				"fieldtype": "Geolocation",
				"label": "POI Location",
				"insert_after": "poi_address",
			},
			{
				"fieldname": "poi_type",
				"fieldtype": "Data",
				"label": "POI Type",
				"insert_after": "poi_location",
			},
			{
				"fieldname": "poi_typecode",
				"fieldtype": "Data",
				"label": "POI Type Code",
				"insert_after": "poi_type",
			},
			{
				"fieldname": "district",
				"fieldtype": "Data",
				"label": "District",
				"insert_after": "poi_typecode",
			},
			{
				"fieldname": "has_valid_phone",
				"fieldtype": "Check",
				"label": "Has Valid Phone",
				"insert_after": "district",
				"default": "0",
			},
			{
				"fieldname": "recommended_product",
				"fieldtype": "Link",
				"label": "Recommended Product",
				"options": "CRM Product",
				"insert_after": "has_valid_phone",
			},
			{
				"fieldname": "ai_call_score",
				"fieldtype": "Int",
				"label": "AI Call Score",
				"insert_after": "recommended_product",
			},
			{
				"fieldname": "ai_call_summary",
				"fieldtype": "Small Text",
				"label": "AI Call Summary",
				"insert_after": "ai_call_score",
			},
		]
	}
	create_custom_fields(custom_fields, ignore_validate=True)
