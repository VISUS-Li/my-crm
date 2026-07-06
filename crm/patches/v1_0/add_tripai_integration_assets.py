import frappe


def execute():
	if frappe.db.exists("CRM TripAI Settings", "CRM TripAI Settings"):
		return

	frappe.get_doc(
		{
			"doctype": "CRM TripAI Settings",
			"enabled": 0,
			"base_url": "http://127.0.0.1:3000",
			"project_key": "nextdevtpl",
			"tool_key": "my-crm",
			"default_redirect_path": "/crm",
		}
	).insert(ignore_permissions=True)
