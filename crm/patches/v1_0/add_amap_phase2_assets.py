import json

import frappe

from crm.fcrm.doctype.crm_view_settings.crm_view_settings import normalize_list_columns


def execute():
	_create_default_settings()
	_create_form_script()
	_create_view_settings()


def _create_default_settings():
	if frappe.db.exists("CRM Amap Settings", "CRM Amap Settings"):
		frappe.db.set_value(
			"CRM Amap Settings",
			"CRM Amap Settings",
			{"enabled": 1},
		)
		return

	frappe.get_doc(
		{
			"doctype": "CRM Amap Settings",
			"enabled": 1,
			"request_interval": 0.35,
			"poi_threshold": 180,
			"max_recursion_depth": 20,
			"import_only_with_phone": 1,
		}
	).insert(ignore_permissions=True)


def _create_form_script():
	name = "Amap Lead Quick Follow-up"
	script = """class CRMLead {
  onLoad() {
    if (!this.doc.amap_poi_id) return

    this.addButton('Mark Contacted', () => {
      this.doc.status = '已联系'
      this.save()
    })

    this.addButton('Mark Interested', () => {
      this.doc.status = '有意向'
      this.save()
    })

    this.addButton('Mark Invalid', () => {
      this.doc.status = '无效'
      this.save()
    })

    this.addButton('Record Follow-up', async () => {
      await this.formDialog({
        title: 'Follow-up note',
        fields: [
          { fieldname: 'note', fieldtype: 'Small Text', label: 'Note', reqd: 1 },
        ],
        primaryAction: {
          label: 'Save',
          action: async (values) => {
            await this.addComment(values.note)
          },
        },
      })
    })
  }
}"""

	if frappe.db.exists("CRM Form Script", name):
		frappe.db.set_value("CRM Form Script", name, "script", script)
		return

	frappe.get_doc(
		{
			"doctype": "CRM Form Script",
			"name": name,
			"dt": "CRM Lead",
			"view": "Form",
			"script": script,
			"enabled": 1,
			"is_standard": 1,
		}
	).insert(ignore_permissions=True)


def _create_view_settings():
	views = [
		{
			"label": "高德-待拨打",
			"icon": "phone",
			"dt": "CRM Lead",
			"type": "list",
			"route_name": "Leads",
			"filters": json.dumps(
				[
					["CRM Lead", "source", "like", "%高德%"],
					["CRM Lead", "has_valid_phone", "=", 1],
					["CRM Lead", "status", "=", "待拨打"],
				]
			),
			"order_by": "modified desc",
			"fieldnames": [
				"lead_name",
				"mobile_no",
				"organization",
				"status",
				"source",
				"district",
				"lead_owner",
			],
		},
		{
			"label": "高德-新线索",
			"icon": "map-pin",
			"dt": "CRM Lead",
			"type": "list",
			"route_name": "Leads",
			"filters": json.dumps(
				[
					["CRM Lead", "source", "like", "%高德%"],
					["CRM Lead", "status", "=", "新线索"],
				]
			),
			"order_by": "modified desc",
			"fieldnames": [
				"lead_name",
				"mobile_no",
				"organization",
				"status",
				"poi_type",
				"district",
				"lead_owner",
			],
		},
	]

	for view in views:
		fieldnames = view.pop("fieldnames")
		view["columns"] = json.dumps(normalize_list_columns(fieldnames, view["dt"]))
		if frappe.db.exists("CRM View Settings", {"label": view["label"], "dt": view["dt"]}):
			continue
		frappe.get_doc(
			{
				"doctype": "CRM View Settings",
				"user": "",
				"public": 1,
				"is_standard": 1,
				"pinned": 0,
				**view,
			}
		).insert(ignore_permissions=True)
