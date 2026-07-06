# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import get_url

from crm.integrations.tripai.auth import (
	get_redirect_path,
	handle_launch_ticket,
	is_tripai_enabled,
)
from crm.integrations.tripai.settings import TripAIConfigError, get_tripai_settings

no_cache = 1


def get_context(context):
	ticket = frappe.form_dict.get("ticket")
	project_key = frappe.form_dict.get("projectKey")

	if not is_tripai_enabled():
		frappe.respond_as_web_page(
			_("TripAI Integration Disabled"),
			_("TripAI integration is not enabled on this site."),
			http_status_code=503,
		)
		return context

	try:
		handle_launch_ticket(ticket, project_key)
	except frappe.AuthenticationError:
		frappe.respond_as_web_page(
			_("Authentication Failed"),
			_("The TripAI launch ticket is invalid or has expired."),
			http_status_code=401,
		)
		return context
	except Exception:
		frappe.log_error(title="TripAI Auth Callback")
		frappe.respond_as_web_page(
			_("Authentication Failed"),
			_("Unable to complete TripAI login. Please try again from the platform."),
			http_status_code=500,
		)
		return context

	redirect_path = get_redirect_path()
	frappe.local.response["type"] = "redirect"
	frappe.local.response["location"] = get_url(redirect_path.lstrip("/"))
	return context
