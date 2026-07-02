"""Amap API error code to user-friendly message mapping."""

from __future__ import annotations

AMAP_ERROR_MESSAGES: dict[str, str] = {
	"USERKEY_PLAT_NOMATCH": (
		"API Key 类型不匹配：请在高德开放平台创建「Web服务」类型的 Key，"
		"不能使用「Web端(JS API)」「Android SDK」「iOS SDK」的 Key。"
		"创建路径：控制台 → 应用管理 → 添加 Key → 选择「Web服务」。"
	),
	"INVALID_USER_KEY": "API Key 无效，请检查是否复制完整或 Key 是否已被删除/禁用。",
	"INVALID_USER_SCODE": "安全密钥(scode)配置错误，Web服务 Key 通常不需要 scode。",
	"INVALID_USER_IP": (
		"服务器 IP 未加入白名单：请在高德控制台该 Key 的「IP白名单」中添加服务器出口 IP "
		"（当前 CRM 服务器：请向运维确认公网/出口 IP）。"
	),
	"USER_DAILY_QUERY_OVER_LIMIT": "该 Key 今日调用配额已用尽，请明天再试或添加备用 Key。",
	"DAILY_QUERY_OVER_LIMIT": "该 Key 今日调用配额已用尽，请明天再试或添加备用 Key。",
	"ACCESS_TOO_FREQUENT": "请求过于频繁，请增大请求间隔后重试。",
	"CUQPS_HAS_EXCEEDED_THE_LIMIT": "并发/QPS 超限，请增大请求间隔或添加备用 Key。",
	"SERVICE_NOT_AVAILABLE": "高德服务暂不可用，请稍后重试。",
}


def format_amap_error(info: str) -> str:
	if not info:
		return "高德 API 返回未知错误"
	if info in AMAP_ERROR_MESSAGES:
		return AMAP_ERROR_MESSAGES[info]
	return f"高德 API 错误：{info}"
