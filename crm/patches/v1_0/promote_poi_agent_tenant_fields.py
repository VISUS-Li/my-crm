import frappe


def execute():
	"""Remove legacy Custom Fields now that agent_tenant_id is a native DocType field."""
	for doctype in ("CRM POI Sync Job", "CRM POI Record"):
		custom_field = frappe.db.get_value(
			"Custom Field",
			{"dt": doctype, "fieldname": "agent_tenant_id"},
			"name",
		)
		if custom_field:
			frappe.delete_doc("Custom Field", custom_field, force=1, ignore_permissions=True)

	frappe.clear_cache(doctype="CRM POI Sync Job")
	frappe.clear_cache(doctype="CRM POI Record")
