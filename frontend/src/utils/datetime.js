/** Strip fractional seconds from DB datetime strings before formatting. */
export function normalizeDatetime(value) {
  if (typeof value !== 'string') return value
  return value.replace(
    /(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2})\.\d+/,
    '$1',
  )
}

function getUserLanguage() {
  return window.sysdefaults?.language || 'en'
}

export function getDefaultDateTimeFormat() {
  const lang = getUserLanguage()
  if (lang === 'zh' || lang.startsWith('zh-')) {
    return 'YYYY年M月D日 HH:mm:ss'
  }
  return 'ddd, MMM D, YYYY h:mm:ss a'
}

export function getLocaleBadgeDateFormat() {
  const lang = getUserLanguage()
  if (lang === 'zh' || lang.startsWith('zh-')) {
    return 'YYYY年M月D日 dddd'
  }
  return 'MMM D, dddd'
}
