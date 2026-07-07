/** Merge boot-time strings with the full translation catalog (API wins on conflict). */
export function mergeTranslatedMessages(bootMessages, apiMessages) {
  return { ...(bootMessages || {}), ...(apiMessages || {}) }
}
