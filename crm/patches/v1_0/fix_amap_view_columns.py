import json

import frappe
from frappe.utils import parse_json

from crm.fcrm.doctype.crm_view_settings.crm_view_settings import normalize_list_columns


def execute():
	for view in frappe.get_all("CRM View Settings", fields=["name", "dt", "columns"]):
		columns = parse_json(view.columns or "[]")
		if not columns or not any(isinstance(column, str) for column in columns):
			continue

		normalized = normalize_list_columns(columns, view.dt)
		frappe.db.set_value(
			"CRM View Settings",
			view.name,
			"columns",
			json.dumps(normalized),
			update_modified=False,
		)
