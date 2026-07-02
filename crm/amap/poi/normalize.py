"""Phone normalization utilities for Amap POI data."""

import re

MOBILE_PATTERN = re.compile(r"^1[3-9]\d{9}$")
LANDLINE_PATTERN = re.compile(r"^0\d{2,3}\d{7,8}$")
SERVICE_NUMBER_PATTERN = re.compile(r"^[48]00\d{7}$")


def normalize_phone(tel: str | None) -> list[str]:
	"""Normalize a raw tel string into a list of valid phone numbers."""
	if not tel:
		return []

	numbers = []
	for part in str(tel).split(";"):
		cleaned = re.sub(r"[\s\-()（）]", "", part.strip())
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
