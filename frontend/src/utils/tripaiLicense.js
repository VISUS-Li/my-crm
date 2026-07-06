const DEVICE_STORAGE_KEY = 'tripai_crm_device_id'

export function getTripAILicenseDeviceId() {
  if (typeof window === 'undefined') {
    return 'crm-web-server'
  }

  let deviceId = window.localStorage.getItem(DEVICE_STORAGE_KEY)
  if (!deviceId) {
    deviceId =
      typeof crypto !== 'undefined' && crypto.randomUUID
        ? `crm-web-${crypto.randomUUID()}`
        : `crm-web-${Date.now()}`
    window.localStorage.setItem(DEVICE_STORAGE_KEY, deviceId)
  }
  return deviceId
}

export function isLicenseError(message = '') {
  const text = String(message)
  return (
    text.includes('license') ||
    text.includes('License') ||
    text.includes('授权') ||
    text.includes('卡密')
  )
}
