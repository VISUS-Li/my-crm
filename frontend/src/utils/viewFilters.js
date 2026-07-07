/**
 * CRM View Settings may store filters as a Frappe filter list
 * ([doctype, field, op, value]) or as a dict for crm.api.doc.get_data.
 */
export function normalizeViewFilters(raw) {
  if (!raw || typeof raw !== 'object') return {}
  if (!Array.isArray(raw)) return raw

  return raw.reduce((acc, filter) => {
    if (!Array.isArray(filter) || filter.length < 3) return acc

    const hasDoctype = filter.length >= 4
    const fieldname = hasDoctype ? filter[1] : filter[0]
    const operator = hasDoctype ? filter[2] : filter[1]
    const value = hasDoctype ? filter[3] : filter[2]

    if (operator === '=' || operator === 'equals') {
      acc[fieldname] = value
    } else {
      acc[fieldname] = [operator, value]
    }

    return acc
  }, {})
}
