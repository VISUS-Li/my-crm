/** Merge translation catalogs; only accept real translations from secondary. */
export function mergeTranslatedMessages(primary, secondary) {
  const merged = { ...(primary || {}) }
  for (const [key, value] of Object.entries(secondary || {})) {
    if (value && value !== key) {
      merged[key] = value
    }
  }
  return merged
}
