const SYNTHETIC_CRM_EMAIL_DOMAIN = 'tripai.local'
const PHONE_TEMP_EMAIL_DOMAINS = ['phone.tripai.icu']

export function isPlaceholderEmail(email = '') {
  const normalized = String(email || '')
    .trim()
    .toLowerCase()
  if (!normalized.includes('@')) return false
  if (normalized.endsWith(`@${SYNTHETIC_CRM_EMAIL_DOMAIN}`)) return true
  const domain = normalized.split('@')[1]
  return PHONE_TEMP_EMAIL_DOMAINS.includes(domain)
}

export function isRealEmail(email = '') {
  const normalized = String(email || '').trim()
  return normalized.includes('@') && !isPlaceholderEmail(normalized)
}

export function formatPhoneDisplay(phone = '') {
  const digits = String(phone || '').replace(/\D/g, '')
  if (!digits) return ''
  if (digits.startsWith('86') && digits.length >= 13) {
    return digits.slice(2)
  }
  return digits
}

export function contactDisplayFromCrmUser(crmUser = '') {
  const value = String(crmUser || '').trim()
  if (!value) return ''
  if (value.endsWith(`@${SYNTHETIC_CRM_EMAIL_DOMAIN}`)) {
    const local = value.split('@')[0]
    return formatPhoneDisplay(local.startsWith('+') ? local : `+${local}`)
  }
  if (isRealEmail(value)) return value
  return value.split('@')[0]
}

export function getUserContactDisplay(user = {}) {
  if (user.contact_display) return user.contact_display
  if (user.tripai_phone) return formatPhoneDisplay(user.tripai_phone)
  if (user.mobile_no) return formatPhoneDisplay(user.mobile_no)
  const email = user.email || user.name || ''
  if (isRealEmail(email)) return email
  return contactDisplayFromCrmUser(email)
}

export function getUserSecondaryContact(user = {}) {
  if (user.secondary_contact) return user.secondary_contact
  if (user.primary_contact_type === 'phone' && isRealEmail(user.tripai_email)) {
    return user.tripai_email
  }
  if (user.primary_contact_type === 'email' && user.tripai_phone) {
    return formatPhoneDisplay(user.tripai_phone)
  }
  return null
}

export function getUserLabel(user = {}) {
  return user.full_name || getUserContactDisplay(user)
}
