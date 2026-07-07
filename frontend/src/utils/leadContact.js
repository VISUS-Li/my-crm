/** Phone / lead URL helpers for lead detail actions. */

export function normalizePhoneForTel(phone) {
  if (!phone) return ''
  return String(phone).replace(/[^\d+]/g, '')
}

export function getLeadPageUrl(leadId) {
  if (!leadId) return ''
  const origin = window.location.origin
  const base = window.crm?.base_url || '/crm'
  const normalizedBase = base.endsWith('/') ? base.slice(0, -1) : base
  return `${origin}${normalizedBase}/leads/${encodeURIComponent(leadId)}`
}

export function isTouchPhoneDevice() {
  if (typeof window === 'undefined') return false
  const coarsePointer = window.matchMedia?.('(pointer: coarse)')?.matches
  const mobileUa = /Android|iPhone|iPad|iPod|Mobile/i.test(
    navigator.userAgent || '',
  )
  return coarsePointer || mobileUa
}
