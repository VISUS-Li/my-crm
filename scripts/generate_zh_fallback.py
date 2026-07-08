#!/usr/bin/env python3
"""Generate frontend/src/locales/zh-fallback.js from Python translation sources."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "frontend" / "src" / "locales" / "zh-fallback.js"

from phone_sales_guide_translations import PHONE_SALES_GUIDE_TRANSLATIONS

# Sidebar, login, workbench, and other CRM UI strings (English msgid -> zh).
CORE_UI_TRANSLATIONS: dict[str, str] = {
    "Sign in to TripAI CRM": "登录 TripAI CRM",
    "Use your TripAI phone number or email": "使用 TripAI 手机号或邮箱登录",
    "Phone or Email": "手机号或邮箱",
    "e.g. 13800138000 or name@example.com": "例如 13800138000 或 name@example.com",
    "Password": "密码",
    "Sign in": "登录",
    "Invalid phone, email, or password": "手机号、邮箱或密码无效",
    "Workbench": "工作台",
    "Pending Calls": "待拨打",
    "Interested": "有意向",
    "Fetch Merchants": "获取商家",
    "Leads": "线索",
    "Call Logs": "通话记录",
    "Tasks": "任务",
    "Notifications": "通知",
    "Help": "帮助",
    "Collapse": "折叠",
    "Expand": "展开",
    "Phone Sales": "电话销售",
    "All Views": "全部视图",
    "Contacted Today": "今日已联系",
    "New Leads": "新线索",
    "{0} merchants waiting for your call": "有 {0} 个商家等待拨打",
    "Start with the first one in the list": "从列表第一个开始拨打",
    "Start Calling": "开始拨打",
    "Recent POI Sync Jobs": "最近同步任务",
    "View All": "查看全部",
    "POI Sync Jobs": "POI 同步任务",
    "No sync jobs yet. Create one to fetch merchant data from Amap.": "还没有同步任务，创建一个即可从高德获取商家数据",
    "No sync jobs yet": "还没有同步任务",
    "Create one to fetch merchant data from Amap.": "创建一个即可从高德获取商家数据",
    "No {0} Found": "未找到{0}",
    "Fetched {0}, {1} with phone, {2} leads created": "抓取 {0} 条，{1} 条有电话，创建 {2} 条线索",
    "Dashboard": "仪表盘",
    "Deals": "商机",
    "Contacts": "联系人",
    "Organizations": "组织",
    "Notes": "备注",
    "Calendar": "日历",
}


def main() -> None:
    merged = {**CORE_UI_TRANSLATIONS, **PHONE_SALES_GUIDE_TRANSLATIONS}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(merged, ensure_ascii=False, indent=2)
    OUT.write_text(
        "/** Bundled zh fallbacks when server .mo is stale (merged before boot/API). */\n"
        f"export const zhFallback = {payload}\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(merged)} entries to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
