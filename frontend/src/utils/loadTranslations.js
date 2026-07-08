import { call, getConfig, setConfig } from 'frappe-ui'
import { zhFallback } from '@/locales/zh-fallback'
import { mergeTranslatedMessages } from '@/utils/mergeTranslatedMessages'

export { mergeTranslatedMessages }

/** Merge bundled zh fallbacks with boot/API (server catalog wins on conflict). */
export function getMergedTranslations(bootMessages = {}) {
  return mergeTranslatedMessages(zhFallback, bootMessages)
}

/** Fetch and apply CRM translations for the current session language. */
export async function loadTranslations() {
  const boot = getMergedTranslations(
    getConfig('translatedMessages') || window.translated_messages || {},
  )
  try {
    const apiMessages = await call('crm.api.get_translations')
    const merged = mergeTranslatedMessages(boot, apiMessages)
    setConfig('translatedMessages', merged)
    window.translated_messages = merged
    return merged
  } catch (error) {
    console.error('Failed to load translations', error)
    setConfig('translatedMessages', boot)
    return boot
  }
}
