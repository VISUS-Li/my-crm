# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and Contributors
# GNU GPLv3 License. See license.txt

import frappe
from frappe import _
from frappe.integrations.frappe_providers.frappecloud_billing import is_fc_site
from frappe.translate import get_all_translations, get_translated_doctypes
from frappe.utils import cint, get_system_timezone
from frappe.utils.telemetry import capture

from crm.utils.i18n import get_session_language

no_cache = 1

# SPA routes that Guest may load without CRM app roles (login, auth callback, welcome).
_GUEST_SPA_SUFFIXES = ("/login", "/welcome")


def _is_guest_allowed_spa_route(request_path: str) -> bool:
	path = (request_path or "").rstrip("/").lower()
	return any(path.endswith(suffix) or f"{suffix}/" in path for suffix in _GUEST_SPA_SUFFIXES)


def get_context():
	_request_path = getattr(getattr(frappe.local, "request", None), "path", "") or ""

	# Allow guest to load public SPA routes (login page, welcome).
	if _is_guest_allowed_spa_route(_request_path):
		frappe.db.commit()
		context = frappe._dict()
		context.boot = get_boot()
		return context

	from crm.api import check_app_permission

	if not check_app_permission():
		frappe.throw(_("You do not have permission to access TripAI CRM"), frappe.PermissionError)

	frappe.db.commit()
	context = frappe._dict()
	context.boot = get_boot()
	if frappe.session.user != "Guest":
		capture("active_site", "crm")
	return context


# TripAI launch_ticket auth is handled by website route tripai_auth_callback (hooks.py).


@frappe.whitelist(methods=["POST"], allow_guest=True)
def get_context_for_dev():
	if not frappe.conf.developer_mode:
		frappe.throw(_("This method is only meant for developer mode"))
	return get_boot()


def get_boot():
	return frappe._dict(
		{
			"frappe_version": frappe.__version__,
			"default_route": get_default_route(),
			"site_name": frappe.local.site,
			"socketio_port": frappe.conf.socketio_port,
			"read_only_mode": frappe.flags.read_only,
			"csrf_token": frappe.sessions.get_csrf_token(),
			"setup_complete": cint(frappe.get_system_settings("setup_complete")),
			"sysdefaults": frappe.defaults.get_defaults(),
			"is_demo_site": frappe.conf.get("is_demo_site"),
			"demo_data_created": frappe.db.get_default("crm_demo_data_created") == "1",
			"is_fc_site": is_fc_site(),
			"show_sales_hierarchy_banner": frappe.db.count("CRM Lead") > 0,
			"phone_sales_mode": _get_phone_sales_mode(),
			"translated_doctypes": get_translated_doctypes(),
			"translated_messages": get_all_translations(get_session_language()),
			"timezone": {
				"system": get_system_timezone(),
				"user": frappe.db.get_value("User", frappe.session.user, "time_zone")
				or get_system_timezone(),
			},
		}
	)


def get_default_route():
	return "/crm"


def _get_phone_sales_mode() -> bool:
	if not frappe.db.exists("DocType", "FCRM Settings"):
		return False
	return bool(frappe.db.get_single_value("FCRM Settings", "enable_phone_sales_mode"))
