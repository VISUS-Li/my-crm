"""Phone and media normalization utilities for Amap POI data."""

import re

MOBILE_PATTERN = re.compile(r"^1[3-9]\d{9}$")
LANDLINE_PATTERN = re.compile(r"^0\d{2,3}\d{7,8}$")
SERVICE_NUMBER_PATTERN = re.compile(r"^[48]00\d{7}$")
PHONE_SPLIT_PATTERN = re.compile(r"[;；,，/、|]+")


def normalize_phone(tel: str | None) -> list[str]:
	"""Normalize a raw tel string into a list of valid phone numbers."""
	if not tel:
		return []

	numbers = []
	for part in PHONE_SPLIT_PATTERN.split(str(tel)):
		cleaned = clean_phone_part(part)
		if not cleaned:
			continue

		if MOBILE_PATTERN.match(cleaned):
			numbers.append(cleaned)
			continue

		if LANDLINE_PATTERN.match(cleaned):
			numbers.append(cleaned)
			continue

		digits = re.sub(r"\D", "", cleaned)
		if MOBILE_PATTERN.match(digits):
			numbers.append(digits)
		elif LANDLINE_PATTERN.match(digits):
			numbers.append(digits)

	return _dedupe(numbers)


def clean_phone_part(part: str | None) -> str:
	return re.sub(r"[\s\-()（）]", "", str(part or "").strip())


def parse_phone_rows(tel: str | None) -> list[dict[str, object]]:
	"""Return all phone-like values, including service numbers, for display/audit."""
	if not tel:
		return []

	rows = []
	seen = set()
	for idx, part in enumerate(PHONE_SPLIT_PATTERN.split(str(tel)), start=1):
		raw = part.strip()
		cleaned = clean_phone_part(raw)
		if not cleaned:
			continue

		digits = re.sub(r"\D", "", cleaned)
		phone_type = "unknown"
		is_valid = False
		normalized = digits

		if MOBILE_PATTERN.match(digits):
			phone_type = "mobile"
			is_valid = True
		elif LANDLINE_PATTERN.match(digits):
			phone_type = "landline"
			is_valid = True
		elif SERVICE_NUMBER_PATTERN.match(digits):
			phone_type = "service"

		key = normalized or cleaned
		if key in seen:
			continue
		seen.add(key)
		rows.append(
			{
				"raw_value": raw,
				"normalized_value": normalized,
				"phone_type": phone_type,
				"is_valid": 1 if is_valid else 0,
				"is_primary": 0,
				"display_order": idx,
			}
		)

	for row in rows:
		if row["is_valid"]:
			row["is_primary"] = 1
			break

	return rows


def parse_photo_rows(photos) -> list[dict[str, object]]:
	if not photos:
		return []

	if isinstance(photos, dict):
		photos = [photos]
	elif isinstance(photos, str):
		photos = [{"url": photos}]
	elif not isinstance(photos, list):
		return []

	rows = []
	for idx, photo in enumerate(photos, start=1):
		if not isinstance(photo, dict):
			continue
		url = photo.get("url") or photo.get("URL") or ""
		if not url:
			continue
		rows.append(
			{
				"title": photo.get("title") or photo.get("name") or "",
				"url": url,
				"display_order": idx,
				"source": "Amap",
			}
		)
	return rows


def get_primary_phone(tel: str | None) -> str | None:
	numbers = normalize_phone(tel)
	return numbers[0] if numbers else None


def has_valid_phone(tel: str | None) -> bool:
	return bool(get_primary_phone(tel))


def filter_service_numbers(numbers: list[str]) -> list[str]:
	return [n for n in numbers if not SERVICE_NUMBER_PATTERN.match(n)]


def _dedupe(numbers: list[str]) -> list[str]:
	seen = set()
	result = []
	for number in numbers:
		if number not in seen:
			seen.add(number)
			result.append(number)
	return result
