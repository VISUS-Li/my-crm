export const FONT_SCALE_STORAGE_KEY = 'fontScale'
export const DEFAULT_FONT_SCALE = 1

/** Allowed font scale steps — font-size only; spacing/heights stay fixed. */
export const FONT_SCALE_OPTIONS = [
  { label: 'Default', value: 1, description: '100%' },
  { label: 'Large', value: 1.125, description: '112.5%' },
  { label: 'Extra Large', value: 1.25, description: '125%' },
]

const ALLOWED_VALUES = FONT_SCALE_OPTIONS.map((o) => o.value)
const MIN_SCALE = Math.min(...ALLOWED_VALUES)
const MAX_SCALE = Math.max(...ALLOWED_VALUES)

export function parseFontScale(value) {
  const n = parseFloat(value)
  if (Number.isNaN(n)) return DEFAULT_FONT_SCALE
  if (ALLOWED_VALUES.includes(n)) return n
  return Math.min(MAX_SCALE, Math.max(MIN_SCALE, n))
}

export function getStoredFontScale() {
  if (typeof localStorage === 'undefined') return DEFAULT_FONT_SCALE
  return parseFontScale(localStorage.getItem(FONT_SCALE_STORAGE_KEY))
}

export function fontScaleCssValue(scale = DEFAULT_FONT_SCALE) {
  return String(parseFontScale(scale))
}
