import frappe

from crm.setup.defaults import apply_chinese_defaults


def execute():
	apply_chinese_defaults()
	frappe.db.commit()
