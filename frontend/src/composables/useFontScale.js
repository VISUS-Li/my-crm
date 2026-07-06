import { ref } from 'vue'
import {
  DEFAULT_FONT_SCALE,
  FONT_SCALE_OPTIONS,
  FONT_SCALE_STORAGE_KEY,
  fontScaleCssValue,
  parseFontScale,
} from '@/utils/fontScale'

const isBrowser = typeof window !== 'undefined'

const currentFontScale = ref(DEFAULT_FONT_SCALE)

function applyFontScale(scale) {
  if (!isBrowser) return
  document.documentElement.style.setProperty(
    '--font-scale',
    fontScaleCssValue(scale),
  )
}

function setFontScale(value) {
  const parsed = parseFontScale(value)
  currentFontScale.value = parsed
  applyFontScale(parsed)
  if (isBrowser) {
    localStorage.setItem(FONT_SCALE_STORAGE_KEY, String(parsed))
  }
}

let initialized = false
function initializeFontScale() {
  if (initialized || !isBrowser) return
  initialized = true
  const stored = localStorage.getItem(FONT_SCALE_STORAGE_KEY)
  setFontScale(stored ?? DEFAULT_FONT_SCALE)
}

export function useFontScale() {
  initializeFontScale()
  return {
    currentFontScale,
    setFontScale,
    initializeFontScale,
    FONT_SCALE_OPTIONS,
  }
}

export { initializeFontScale }
