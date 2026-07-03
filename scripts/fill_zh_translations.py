#!/usr/bin/env python3
"""Fill missing Chinese translations in crm/locale/zh.po without reformatting the file."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ZH_PO = ROOT / "crm" / "locale" / "zh.po"

from i18n_translations import BULK_TRANSLATIONS

# fmt: off
TRANSLATIONS: dict[str, str] = {
    "Access Denied": "访问被拒绝",
    "Accept Call": "接听来电",
    "Access token is required": "需要访问令牌",
    "Account Info & Security": "账户信息与安全",
    "Activity Timeline": "活动时间线",
    "Add ({0})": "添加（{0}）",
    "Add Attendee": "添加参与者",
    "Add CRM Product": "添加 CRM 产品",
    "Add Chart": "添加图表",
    "Add Condition": "添加条件",
    "Add Condition Group": "添加条件组",
    "Add Description": "添加描述",
    "Add Description.": "添加描述。",
    "Add Email": "添加电子邮件",
    "Add Location": "添加位置",
    "Add Mobile Number...": "添加手机号...",
    "Add Note": "添加备注",
    "Add Notification": "添加通知",
    "Add Organization...": "添加组织...",
    "Add Sample Data": "添加示例数据",
    "Add Task": "添加任务",
    "Add User": "添加用户",
    "Add Users": "添加用户",
    "Add a Condition": "添加条件",
    "Add a Custom Condition": "添加自定义条件",
    "Add a Task": "添加任务",
    "Add a name for your source": "为来源添加名称",
    "Add direct reports": "添加直属下属",
    "Add one to get started.": "添加一个以开始使用。",
    "Add time targets around support milestones like first response": "为支持里程碑（如首次响应）添加时间目标",
    "Add, edit, and manage sources for automatic lead syncing to your CRM": "添加、编辑和管理线索自动同步来源",
    "All Day Event Notifications": "全天事件通知",
    "All available priorities have already been added": "所有可用优先级均已添加",
    "Any failed lead syncs will show up here": "失败的线索同步将显示在此处",
    "Appearance": "外观",
    "Are you sure you want to clear demo data? This action cannot be undone.": "确定要清除演示数据吗？此操作无法撤销。",
    "Are you sure you want to remove this tab and all its content?": "确定要删除此标签页及其所有内容吗？",
    "Assign Condition is required": "必须填写分配条件",
    "A lead sync source is already enabled for this Facebook Lead Form!": "此 Facebook 线索表单已启用同步来源！",
    "A {0} cannot report to a {1}": "{0} 不能向 {1} 汇报",
    "No New Notifications": "暂无新通知",
    "Settings saved": "设置已保存",
    "You have no new notifications": "您没有新通知",
    "You have no events scheduled": "您没有已安排的事件",
    "Manage your lead sources here. Add new sources to start syncing leads automatically.": "在此管理线索来源。添加新来源以自动同步线索。",
    "Set": "已设置",
    "Not Set": "未设置",
    "Yes": "是",
    "No": "否",
    "Monday": "星期一",
    "Tuesday": "星期二",
    "Wednesday": "星期三",
    "Thursday": "星期四",
    "Friday": "星期五",
    "Saturday": "星期六",
    "Sunday": "星期日",
    "Low": "低",
    "Medium": "中",
    "High": "高",
    "Lead": "线索",
    "Deal": "商机",
    "Sales Hierarchy": "销售层级",
    "Lead Data": "线索数据",
    "Replied": "已回复",
    "Contacted": "已联系",
    "Nurture": "培育中",
    "Qualified": "已合格",
    "Converted": "已转化",
    "Unqualified": "不合格",
    "Junk": "垃圾线索",
    "Qualification": "资格确认",
    "Demo/Making": "演示/制作",
    "Proposal/Quotation": "方案/报价",
    "Negotiation": "谈判中",
    "Ready to Close": "即将成交",
    "Existing Customer": "现有客户",
    "Reference": "推荐",
    "Advertisement": "广告",
    "Cold Calling": "电话开发",
    "Exhibition": "展会",
    "Supplier Reference": "供应商推荐",
    "Mass Mailing": "群发邮件",
    "Customer's Vendor": "客户供应商",
    "Campaign": "营销活动",
    "Walk In": "上门拜访",
    "Website": "网站",
    "Pricing": "价格",
    "Competition": "竞争",
    "Budget Constraints": "预算限制",
    "Missing Features": "缺少功能",
    "Long Sales Cycle": "销售周期过长",
    "No Decision-Maker": "无决策者",
    "Unresponsive Prospect": "客户无响应",
    "Poor Fit": "不匹配",
    "Other": "其他",
    "Draft": "草稿",
    "Running": "运行中",
    "Cancelled": "已取消",
    "Amap Settings": "高德设置",
    "Amap POI": "高德 POI",
    "POI Sync Jobs": "POI 同步任务",
    "Mock Mode": "模拟模式",
    "Global Settings": "全局设置",
    "New Job": "新建任务",
    "Enable Amap POI Sync": "启用高德 POI 同步",
    "Use Mock API": "使用模拟 API",
    "Turn on POI collection for all agents": "为所有代理开启 POI 采集",
    "Test the full flow without Amap API keys": "无需高德 API 密钥即可测试完整流程",
    "Test Connection": "测试连接",
    "Request Interval (s)": "请求间隔（秒）",
    "POI Threshold": "POI 阈值",
    "Max Recursion Depth": "最大递归深度",
    "Default Lead Owner": "默认线索负责人",
    "Default Product": "默认产品",
    "Import only POIs with valid phone": "仅导入有有效电话的 POI",
    "API Keys": "API 密钥",
    "Add Key": "添加密钥",
    "No API keys configured. Enable mock mode or add keys here.": "未配置 API 密钥。请启用模拟模式或在此添加密钥。",
    "Remark": "备注",
    "Back to Jobs": "返回任务列表",
    "Connection successful": "连接成功",
    "Connection failed": "连接失败",
    "Sync started": "同步已开始",
    "Failed to start sync": "启动同步失败",
    "Job Detail": "任务详情",
    "Start Sync": "开始同步",
    "Total POI": "POI 总数",
    "With Phone": "有电话",
    "Progress": "进度",
    "Error Log": "错误日志",
    "Skipped": "已跳过",
    "Started": "开始时间",
    "Preview Results": "预览结果",
    "No phone": "无电话",
    "Create a sync job to fetch POI data from Amap by city, district, and industry keywords.": "创建同步任务，按城市、区县和行业关键词从高德获取 POI 数据。",
    "{0} POI / {1} leads": "{0} 个 POI / {1} 条线索",
    "Amap POI sync is disabled in settings": "设置中已禁用高德 POI 同步",
    "Starting sync": "正在启动同步",
    "Unable to resolve search bounds from bbox or adcode.": "无法从边界框或行政区划代码解析搜索范围。",
    "Fetching POI data with quadtree...": "正在使用四叉树获取 POI 数据...",
    "Fetching POI data via city text search...": "正在通过城市文本搜索获取 POI 数据...",
    "Importing {0} POI records...": "正在导入 {0} 条 POI 记录...",
    "Sync completed successfully": "同步成功完成",
    "Sync failed": "同步失败",
    "Queued for processing": "已排队等待处理",
    "Enable Amap POI sync or mock mode in settings first": "请先在设置中启用高德 POI 同步或模拟模式",
    "Preview search failed": "预览搜索失败",
    "Mock API mode enabled": "已启用模拟 API 模式",
    "No API keys configured": "未配置 API 密钥",
    "Accounting": "会计",
    "Advertising": "广告",
    "Aerospace": "航空航天",
    "Agriculture": "农业",
    "Airline": "航空",
    "Apparel & Accessories": "服装与配饰",
    "Automotive": "汽车",
    "Banking": "银行",
    "Biotechnology": "生物技术",
    "Broadcasting": "广播",
    "Brokerage": "经纪",
    "Chemical": "化工",
    "Computer": "计算机",
    "Consulting": "咨询",
    "Consumer Products": "消费品",
    "Cosmetics": "化妆品",
    "Defense": "国防",
    "Department Stores": "百货商店",
    "Education": "教育",
    "Electronics": "电子",
    "Energy": "能源",
    "Entertainment & Leisure, Executive Search": "娱乐休闲、高管猎聘",
    "Financial Services": "金融服务",
    "Food": "食品",
    "Beverage & Tobacco": "饮料与烟草",
    "Grocery": "杂货",
    "Health Care": "医疗保健",
    "Internet Publishing": "互联网出版",
    "Investment Banking": "投资银行",
    "Legal": "法律",
    "Manufacturing": "制造业",
    "Motion Picture & Video": "影视",
    "Music": "音乐",
    "Newspaper Publishers": "报纸出版",
    "Online Auctions": "在线拍卖",
    "Pension Funds": "养老基金",
    "Pharmaceuticals": "制药",
    "Private Equity": "私募股权",
    "Publishing": "出版",
    "Real Estate": "房地产",
    "Retail & Wholesale": "零售与批发",
    "Securities & Commodity Exchanges": "证券与商品交易所",
    "Service": "服务业",
    "Soap & Detergent": "肥皂与洗涤剂",
    "Software": "软件",
    "Sports": "体育",
    "Technology": "科技",
    "Telecommunications": "电信",
    "Television": "电视",
    "Transportation": "运输",
    "Transportation Equipment": "运输设备",
    "Utilities": "公用事业",
    "Venture Capital": "风险投资",
    "Auto-rotate": "自动轮换",
    "Assign by workload": "按工作量分配",
    "Low-Medium": "偏低",
    "Medium-High": "偏高",
    "Created On": "创建时间",
    "Modified By": "修改人",
    "Created By": "创建人",
    "Last Updated By": "最后更新人",
    "Last Updated On": "最后更新时间",
    "Tags": "标签",
    "Incoming": "来电",
    "Outgoing": "去电",
    "Service not supported": "不支持的服务",
    "Could not create email account: {0}": "无法创建邮件账户：{0}",
    "Call from {0} to {1}": "从 {0} 呼叫 {1}",
    "Event Reminder: {0}": "事件提醒：{0}",
    "Event Reminder": "事件提醒",
    "This is a reminder for your upcoming event:": "这是您即将开始的事件提醒：",
    "Start Time:": "开始时间：",
    "Time Remaining:": "剩余时间：",
    "This is an automated reminder from your calendar system.": "这是日历系统自动发送的提醒。",
    "minute(s)": "分钟",
    "hour(s)": "小时",
    "day(s)": "天",
    "week(s)": "周",
    "unit(s)": "单位",
    "{0} {1}": "{0} {1}",
    "Grid reached minimum span, stopping split": "网格已达最小跨度，停止拆分",
    "Reached max recursion depth, stopping split": "已达最大递归深度，停止拆分",
    "No Activities Found": "暂无活动",
    "No Emails Found": "暂无邮件",
    "No Comments Found": "暂无评论",
    "No Data Fields Added Yet": "尚未添加数据字段",
    "No Call History": "暂无通话记录",
    "No Notes Found": "暂无备注",
    "No Tasks Found": "暂无任务",
    "No Attachments Found": "暂无附件",
    "No WhatsApp Messages Found": "暂无 WhatsApp 消息",
    "There are no activities to display here. Go ahead and make some changes.": "此处暂无活动。您可以开始添加一些内容。",
    "No emails found in your inbox. New messages will appear here soon.": "收件箱暂无邮件。新消息将很快显示在此处。",
    "Be the first to add one.": "成为第一个添加的人。",
    "No data fields have been added yet.": "尚未添加任何数据字段。",
    "No recent calls to display. Log a call or call someone now!": "暂无最近通话。立即记录或发起通话！",
    "Nothing here for now. Add a note to keep track of things.": "暂无内容。添加备注以便跟踪。",
    "Nothing to do at the moment. Start organizing by adding one here.": "当前暂无待办。在此添加任务开始整理。",
    "No files have been attached yet. Upload files to see them here.": "尚未上传附件。上传文件后将显示在此处。",
    "Start a conversation now!": "立即开始对话！",
    "No Upcoming Events": "暂无即将到来的事件",
    "No Assignment Rules Found": "未找到分配规则",
    "Connection successful, Web服务 Key is valid": "连接成功，Web服务 Key 有效",
    "No API keys configured. Please add and save one first.": "未配置 API Key，请先添加并保存",
    "Invalid JSON response: {0}": "无效的 JSON 响应：{0}",
    "Request failed after {0} retries": "请求在 {0} 次重试后失败",
    "Error while creating quotation in ERPNext": "在 ERPNext 中创建报价单时出错",
    "Error while creating quotation in ERPNext. Check error log in ERPNext for more details": "在 ERPNext 中创建报价单时出错。请查看 ERPNext 错误日志了解详情",
    "You have been invited to join {0}": "您已被邀请加入 {0}",
    "and": "且",
    "or": "或",
}
# fmt: on


def escape_po(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def fill_empty_msgstr(content: str) -> tuple[str, int]:
    updated = 0

    def replacer(match: re.Match[str]) -> str:
        nonlocal updated
        msgid = match.group(1)
        translation = TRANSLATIONS.get(msgid)
        if translation is None:
            return match.group(0)
        updated += 1
        return f'msgid "{escape_po(msgid)}"\nmsgstr "{escape_po(translation)}"'

    pattern = re.compile(r'msgid "((?:\\.|[^"\\])*)"\nmsgstr ""', re.MULTILINE)
    return pattern.sub(replacer, content), updated


def append_missing(content: str) -> tuple[str, int]:
    existing = set(re.findall(r'msgid "((?:\\.|[^"\\])*)"', content))
    appended = 0
    blocks: list[str] = []
    for msgid, msgstr in TRANSLATIONS.items():
        if msgid in existing:
            continue
        blocks.append(f'\nmsgid "{escape_po(msgid)}"\nmsgstr "{escape_po(msgstr)}"\n')
        appended += 1
    if blocks:
        if not content.endswith("\n"):
            content += "\n"
        content += "".join(blocks)
    return content, appended


def main() -> None:
    TRANSLATIONS.update(BULK_TRANSLATIONS)
    content = ZH_PO.read_text(encoding="utf-8")
    content, filled = fill_empty_msgstr(content)
    content, appended = append_missing(content)
    ZH_PO.write_text(content, encoding="utf-8")
    print(f"Filled {filled} empty translations, appended {appended} new entries")


if __name__ == "__main__":
    main()
