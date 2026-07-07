/**
 * Human-readable label for Frappe naming-series document IDs.
 * e.g. CRM-LEAD-2026-00359 → "Lead #359" (zh: "线索 #359")
 */
export function formatDocumentId(docId, doctypeKey = 'Lead') {
  if (!docId) return { display: '', full: '' }

  const typeLabel = __(String(doctypeKey).replace(/^CRM\s+/, ''))
  const match = String(docId).match(/-(\d+)$/)
  const seq = match ? match[1].replace(/^0+/, '') || match[1] : null

  if (seq) {
    return {
      display: __('{0} #{1}', [typeLabel, seq]),
      full: docId,
    }
  }

  return {
    display: __('{0}: {1}', [typeLabel, docId]),
    full: docId,
  }
}

export function formatReferenceName(name, doctypeKey = 'Lead') {
  if (!name) return ''
  if (String(name).startsWith('CRM-')) {
    return formatDocumentId(name, doctypeKey).display
  }
  return name
}
