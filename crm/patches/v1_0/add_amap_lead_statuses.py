import frappe


LEAD_STATUSES = [
	{"lead_status": "新线索", "type": "Open", "color": "blue", "position": 10},
	{"lead_status": "待拨打", "type": "Open", "color": "orange", "position": 11},
	{"lead_status": "已联系", "type": "Open", "color": "cyan", "position": 12},
	{"lead_status": "有意向", "type": "Open", "color": "green", "position": 13},
	{"lead_status": "演示/试用", "type": "Ongoing", "color": "teal", "position": 14},
	{"lead_status": "报价", "type": "Ongoing", "color": "purple", "position": 15},
	{"lead_status": "未接", "type": "Open", "color": "gray", "position": 16},
	{"lead_status": "无效", "type": "Lost", "color": "red", "position": 17},
	{"lead_status": "AI已联系-高意向", "type": "Open", "color": "green", "position": 18},
	{"lead_status": "AI已联系-低意向", "type": "Lost", "color": "gray", "position": 19},
]


def execute():
	for status in LEAD_STATUSES:
		if frappe.db.exists("CRM Lead Status", status["lead_status"]):
			continue
		frappe.get_doc({"doctype": "CRM Lead Status", **status}).insert(ignore_permissions=True)
