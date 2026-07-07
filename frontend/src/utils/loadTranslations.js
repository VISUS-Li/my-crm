import { call, getConfig, setConfig } from 'frappe-ui'
import { mergeTranslatedMessages } from '@/utils/mergeTranslatedMessages'

export { mergeTranslatedMessages }

/** Fetch and apply CRM translations for the current session language. */
export async function loadTranslations() {
  const boot = getConfig('translatedMessages') || window.translated_messages || {}
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
