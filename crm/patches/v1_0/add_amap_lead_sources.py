import frappe


LEAD_SOURCES = [
	"高德地图",
	"高德地图-餐饮",
	"高德地图-美容",
	"高德地图-教培",
	"高德地图-零售",
]


def execute():
	for source_name in LEAD_SOURCES:
		frappe.get_doc(
			{"doctype": "CRM Lead Source", "source_name": source_name}
		).insert(ignore_if_duplicate=True)
