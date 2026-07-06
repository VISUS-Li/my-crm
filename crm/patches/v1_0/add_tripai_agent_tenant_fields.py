import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	custom_fields = {
		"User": [
			{
				"fieldname": "tripai_agent_tenant_id",
				"fieldtype": "Data",
				"label": "TripAI Agent Tenant ID",
				"insert_after": "mobile_no",
				"read_only": 1,
				"hidden": 1,
			},
		],
		"CRM Lead": [
			{
				"fieldname": "tripai_agent_tenant_id",
				"fieldtype": "Data",
				"label": "TripAI Agent Tenant",
				"insert_after": "has_valid_phone",
				"read_only": 1,
				"hidden": 1,
			},
		],
		"CRM POI Sync Job": [
			{
				"fieldname": "agent_tenant_id",
				"fieldtype": "Data",
				"label": "Agent Tenant ID",
				"insert_after": "job_owner",
				"read_only": 1,
				"in_standard_filter": 1,
			},
		],
		"CRM POI Record": [
			{
				"fieldname": "agent_tenant_id",
				"fieldtype": "Data",
				"label": "Agent Tenant ID",
				"insert_after": "job_owner",
				"read_only": 1,
				"in_standard_filter": 1,
			},
		],
	}
	create_custom_fields(custom_fields, ignore_validate=True)
