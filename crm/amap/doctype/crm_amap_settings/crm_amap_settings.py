# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class CRMAmapSettings(Document):
	@frappe.whitelist()
	def test_connection(self):
		from crm.amap.poi.client import build_client_from_settings

		client = build_client_from_settings(self)
		return client.test_connection()

	def get_api_key_list(self) -> list[str]:
		keys = []
		for row in self.api_keys or []:
			key = row.get_password("api_key")
			if key:
				keys.append(key)
		return keys
