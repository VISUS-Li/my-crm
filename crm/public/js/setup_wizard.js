frappe.provide('crm.setup');

frappe.setup.on('before_load', function () {
	const welcome = frappe.setup.slides_settings?.find((slide) => slide.name === 'welcome');
	if (!welcome) return;

	const defaults = {
		language: 'Chinese (Simplified)',
		country: 'China',
		timezone: 'Asia/Shanghai',
		currency: 'CNY',
	};

	for (const field of welcome.fields) {
		if (defaults[field.fieldname]) {
			field.default = defaults[field.fieldname];
		}
	}

	if (frappe.wizard?.values) {
		Object.assign(frappe.wizard.values, defaults);
	}
});
