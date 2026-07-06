# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors

from __future__ import annotations

import re

import requests

from crm.integrations.tripai.auth import handle_launch_ticket
from crm.integrations.tripai.settings import TripAIConfigError, get_tripai_settings

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class TripAIRelayAuthError(Exception):
	def __init__(self, message: str, status_code: int | None = None):
		super().__init__(message)
		self.status_code = status_code


def normalize_phone_input(raw: str) -> str | None:
	trimmed = (raw or "").strip()
	if not trimmed:
		return None
	if trimmed.startswith("+"):
		digits = re.sub(r"\D", "", trimmed[1:])
		if 8 <= len(digits) <= 15:
			return f"+{digits}"
		return None
	digits = re.sub(r"\D", "", trimmed)
	if len(digits) == 11 and digits.startswith("1"):
		return f"+86{digits}"
	if 8 <= len(digits) <= 15:
		return f"+{digits}"
	return None


def is_phone_like(login_id: str) -> bool:
	if EMAIL_PATTERN.match((login_id or "").strip()):
		return False
	return normalize_phone_input(login_id) is not None


def _parse_cookie_header(response: requests.Response) -> str:
	if response.cookies:
		return "; ".join(f"{name}={value}" for name, value in response.cookies.items())

	parts: list[str] = []
	for header in response.headers.get("Set-Cookie", "").split(","):
		chunk = header.split(";", 1)[0].strip()
		if chunk:
			parts.append(chunk)
	return "; ".join(parts)


def tripai_sign_in(login_id: str, password: str) -> str:
	settings = get_tripai_settings()
	base_url = settings["base_url"]
	password = (password or "").strip()
	if not password:
		raise TripAIRelayAuthError("Password is required", 400)

	if is_phone_like(login_id):
		phone_number = normalize_phone_input(login_id)
		if not phone_number:
			raise TripAIRelayAuthError("Invalid phone number", 400)
		url = f"{base_url}/api/auth/sign-in/phone-number"
		payload = {"phoneNumber": phone_number, "password": password, "rememberMe": True}
	else:
		email = (login_id or "").strip().lower()
		if not EMAIL_PATTERN.match(email):
			raise TripAIRelayAuthError("Enter a valid phone number or email", 400)
		url = f"{base_url}/api/auth/sign-in/email"
		payload = {"email": email, "password": password, "rememberMe": True}

	try:
		response = requests.post(url, json=payload, timeout=30)
	except requests.RequestException as exc:
		raise TripAIRelayAuthError(
			f"Cannot reach TripAI at {base_url}. Ensure TripAI is running and CRM server can access it.",
			503,
		) from exc
	try:
		body = response.json()
	except ValueError:
		body = {}

	if not response.ok:
		message = body.get("message") or body.get("error") or f"TripAI login failed ({response.status_code})"
		raise TripAIRelayAuthError(str(message), response.status_code)

	cookie = _parse_cookie_header(response)
	if not cookie:
		raise TripAIRelayAuthError("TripAI login succeeded but no session cookie was returned", 502)

	return cookie


def tripai_create_launch_ticket(session_cookie: str) -> str:
	settings = get_tripai_settings()
	url = f"{settings['base_url']}/api/platform/tools/{settings['tool_key']}/launch"
	try:
		response = requests.get(
			url,
			params={"projectKey": settings["project_key"]},
			headers={"Cookie": session_cookie},
			timeout=30,
		)
	except requests.RequestException as exc:
		raise TripAIRelayAuthError(
			f"Cannot reach TripAI at {settings['base_url']}. Ensure TripAI is running and CRM server can access it.",
			503,
		) from exc
	try:
		body = response.json()
	except ValueError:
		body = {}

	if not response.ok or not body.get("ticket"):
		message = body.get("message") or body.get("error") or f"Launch ticket failed ({response.status_code})"
		raise TripAIRelayAuthError(str(message), response.status_code)

	return str(body["ticket"])


def handle_direct_login(login_id: str, password: str) -> dict:
	"""Authenticate with TripAI (phone or email) and establish CRM session."""
	try:
		settings = get_tripai_settings()
	except TripAIConfigError as exc:
		raise TripAIRelayAuthError(str(exc), 503) from exc

	if not settings["enabled"]:
		raise TripAIRelayAuthError("TripAI integration is disabled", 503)

	session_cookie = tripai_sign_in(login_id, password)
	ticket = tripai_create_launch_ticket(session_cookie)
	result = handle_launch_ticket(ticket, settings["project_key"])
	result["redirect_to"] = settings["default_redirect_path"] or "/crm"
	return result
