import json

import frappe


def execute():
	_create_default_settings()
	_create_form_script()
	_create_view_settings()


def _create_default_settings():
	if frappe.db.exists("CRM Amap Settings", "CRM Amap Settings"):
		frappe.db.set_value(
			"CRM Amap Settings",
			"CRM Amap Settings",
			{"enabled": 1, "use_mock_api": 1},
		)
		return

	frappe.get_doc(
		{
			"doctype": "CRM Amap Settings",
			"enabled": 1,
			"use_mock_api": 1,
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

    this.addButton('标记已联系', () => {
      this.doc.status = '已联系'
      this.save()
    })

    this.addButton('标记有意向', () => {
      this.doc.status = '有意向'
      this.save()
    })

    this.addButton('标记无效', () => {
      this.doc.status = '无效'
      this.save()
    })

    this.addButton('记录跟进', async () => {
      await this.formDialog({
        title: '跟进备注',
        fields: [
          { fieldname: 'note', fieldtype: 'Small Text', label: '备注', reqd: 1 },
        ],
        primaryAction: {
          label: '保存',
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
			"columns": json.dumps(
				[
					"lead_name",
					"mobile_no",
					"organization",
					"status",
					"source",
					"district",
					"lead_owner",
				]
			),
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
			"columns": json.dumps(
				[
					"lead_name",
					"mobile_no",
					"organization",
					"status",
					"poi_type",
					"district",
					"lead_owner",
				]
			),
		},
	]

	for view in views:
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
