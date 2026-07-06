# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors

"""TripAI user contact resolution — phone-first display, aligned with TripAI platform."""

from __future__ import annotations

import re
from typing import Any, Literal

import frappe

ContactType = Literal["phone", "email"]

# TripAI phone-registration placeholder domain (see NextDevTpl AUTH_PHONE_TEMP_EMAIL_DOMAIN)
DEFAULT_PHONE_TEMP_EMAIL_DOMAIN = "phone.tripai.icu"
SYNTHETIC_CRM_EMAIL_DOMAIN = "tripai.local"


def get_phone_temp_email_domains() -> tuple[str, ...]:
	raw = frappe.conf.get("tripai_phone_temp_email_domain") or DEFAULT_PHONE_TEMP_EMAIL_DOMAIN
	parts = [part.strip().lower() for part in str(raw).split(",") if part.strip()]
	return tuple(parts or (DEFAULT_PHONE_TEMP_EMAIL_DOMAIN,))


def is_placeholder_email(email: str | None) -> bool:
	if not email or "@" not in email:
		return False
	normalized = email.strip().lower()
	if normalized.endswith(f"@{SYNTHETIC_CRM_EMAIL_DOMAIN}"):
		return True
	domain = normalized.split("@", 1)[1]
	return domain in get_phone_temp_email_domains()


def is_real_email(email: str | None) -> bool:
	if not email or "@" not in email:
		return False
	return not is_placeholder_email(email)


def normalize_phone_digits(phone: str | None) -> str:
	if not phone:
		return ""
	return re.sub(r"\D", "", phone.strip())


def format_phone_display(phone: str | None, *, mask: bool = False) -> str:
	digits = normalize_phone_digits(phone)
	if not digits:
		return ""

	display = digits
	if digits.startswith("86") and len(digits) >= 13:
		display = digits[2:]
	elif digits.startswith("86") and len(digits) == 11:
		display = digits

	if mask and len(display) >= 7:
		return f"{display[:3]}****{display[-4:]}"
	return display


def extract_tripai_phone(tripai_user: dict[str, Any]) -> str | None:
	phone_raw = (tripai_user.get("phone") or "").strip()
	if normalize_phone_digits(phone_raw):
		return phone_raw

	email_raw = (tripai_user.get("email") or "").strip()
	if email_raw and "@" not in email_raw and normalize_phone_digits(email_raw):
		return email_raw

	if email_raw and is_placeholder_email(email_raw):
		local_part = email_raw.split("@", 1)[0]
		digits = normalize_phone_digits(local_part)
		if digits:
			return f"+{digits}"

	return None


def extract_tripai_real_email(tripai_user: dict[str, Any]) -> str | None:
	email_raw = (tripai_user.get("email") or "").strip().lower()
	if is_real_email(email_raw):
		return email_raw
	return None


def resolve_primary_contact(tripai_user: dict[str, Any], *, mask_phone: bool = False) -> dict[str, Any]:
	"""Resolve primary contact for display. Phone takes precedence over real email."""
	phone_raw = extract_tripai_phone(tripai_user)
	real_email = extract_tripai_real_email(tripai_user) or ""

	if phone_raw:
		return {
			"type": "phone",
			"value": phone_raw,
			"display": format_phone_display(phone_raw, mask=mask_phone),
			"tripai_phone": phone_raw,
			"tripai_email": real_email or None,
		}

	if real_email:
		return {
			"type": "email",
			"value": real_email,
			"display": real_email.lower(),
			"tripai_phone": None,
			"tripai_email": real_email.lower(),
		}

	email_raw = (tripai_user.get("email") or "").strip()
	fallback = email_raw or tripai_user.get("id") or ""
	return {
		"type": "email",
		"value": fallback,
		"display": fallback,
		"tripai_phone": None,
		"tripai_email": None,
	}


def resolve_secondary_contact(primary: dict[str, Any]) -> str | None:
	if primary.get("type") == "phone" and primary.get("tripai_email"):
		return primary["tripai_email"]
	if primary.get("type") == "email" and primary.get("tripai_phone"):
		return format_phone_display(primary["tripai_phone"])
	return None


def normalize_tripai_user_id(tripai_user: dict[str, Any]) -> str:
	"""Stable Frappe User.name — phone users use +{digits}@tripai.local, email users use real email."""
	phone_raw = extract_tripai_phone(tripai_user)
	phone_digits = normalize_phone_digits(phone_raw)
	if phone_digits:
		return f"+{phone_digits}@{SYNTHETIC_CRM_EMAIL_DOMAIN}"

	email = extract_tripai_real_email(tripai_user)
	if email:
		return email

	user_id = tripai_user.get("id") or frappe.generate_hash(length=12)
	return f"{user_id}@{SYNTHETIC_CRM_EMAIL_DOMAIN}"


def contact_display_from_crm_user(crm_user: str) -> str | None:
	"""Derive display contact from synthetic CRM User.name when Link row is missing."""
	if not crm_user:
		return None
	if crm_user.endswith(f"@{SYNTHETIC_CRM_EMAIL_DOMAIN}"):
		local = crm_user.split("@", 1)[0]
		if local.startswith("+"):
			return format_phone_display(local)
		return local
	if is_real_email(crm_user):
		return crm_user
	return crm_user.split("@", 1)[0]


def build_user_link_contact_fields(tripai_user: dict[str, Any]) -> dict[str, Any]:
	primary = resolve_primary_contact(tripai_user)
	secondary = resolve_secondary_contact(primary)
	return {
		"tripai_phone": primary.get("tripai_phone"),
		"tripai_email": primary.get("tripai_email"),
		"primary_contact_type": primary["type"].title(),
		"contact_display": primary["display"],
		"secondary_contact": secondary,
	}


def build_session_contact_fields(link_row: dict[str, Any] | None, crm_user: str) -> dict[str, Any]:
	if link_row:
		display = link_row.get("contact_display") or contact_display_from_crm_user(crm_user)
		return {
			"is_tripai_user": True,
			"contact_display": display,
			"primary_contact_type": (link_row.get("primary_contact_type") or "").lower() or None,
			"tripai_phone": link_row.get("tripai_phone"),
			"tripai_email": link_row.get("tripai_email"),
			"secondary_contact": link_row.get("secondary_contact"),
		}

	display = contact_display_from_crm_user(crm_user)
	if display and crm_user.endswith(f"@{SYNTHETIC_CRM_EMAIL_DOMAIN}"):
		return {
			"is_tripai_user": True,
			"contact_display": display,
			"primary_contact_type": "phone",
			"tripai_phone": None,
			"tripai_email": None,
			"secondary_contact": None,
		}

	return {
		"is_tripai_user": False,
		"contact_display": display or crm_user,
		"primary_contact_type": "email" if is_real_email(crm_user) else None,
		"tripai_phone": None,
		"tripai_email": crm_user if is_real_email(crm_user) else None,
		"secondary_contact": None,
	}


# Backward-compatible alias used by existing tests/callers
normalize_tripai_email = normalize_tripai_user_id
