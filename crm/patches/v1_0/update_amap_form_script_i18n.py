"""Refresh Amap lead form script msgids and re-apply Chinese locale defaults."""

import frappe

from crm.patches.v1_0.add_amap_phase2_assets import _create_form_script
from crm.setup.defaults import apply_chinese_defaults


def execute():
	apply_chinese_defaults()
	_create_form_script()
	frappe.db.commit()
