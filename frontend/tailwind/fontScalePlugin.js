import plugin from 'tailwindcss/plugin'
import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))

// frappe-ui does not export ./tailwind/generated/* in package.json exports;
// read the file from node_modules directly (Tailwind/PostCSS runs in Node).
const typographyTokens = JSON.parse(
  readFileSync(
    join(__dirname, '../node_modules/frappe-ui/tailwind/generated/typography.json'),
    'utf8',
  ),
)

const SCALE_VAR = 'var(--font-scale, 1)'
const WEIGHT_VARIANTS = ['medium', 'semibold', 'bold', 'black']

function scaleFontSize(px) {
  return `calc(${px} * ${SCALE_VAR})`
}

/** Keep line-height in fixed px so row/button heights do not grow with font scale. */
function fixedLineHeightPx(fontSizePx, lineHeightRatio) {
  const size = parseFloat(fontSizePx)
  const ratio = parseFloat(lineHeightRatio)
  return `${Math.round(size * ratio * 1000) / 1000}px`
}

function buildScaledFontSize() {
  const out = {}
  for (const [key, [size, meta]] of Object.entries(typographyTokens.fontSize)) {
    out[key] = [
      scaleFontSize(size),
      {
        ...meta,
        lineHeight: meta.lineHeight
          ? fixedLineHeightPx(size, meta.lineHeight)
          : meta.lineHeight,
      },
    ]
  }
  for (const [key, p] of Object.entries(typographyTokens.paragraph || {})) {
    const orig = typographyTokens.fontSize[key]
    if (!orig) continue
    const [origSize, meta] = orig
    out[`p-${key}`] = [
      scaleFontSize(origSize),
      {
        ...meta,
        lineHeight: fixedLineHeightPx(origSize, p.lineHeight),
        letterSpacing: p.letterSpacing,
      },
    ]
  }
  return out
}

function buildScaledTextStyleUtilities() {
  const out = {}
  const t = typographyTokens
  const groups = [
    {
      className: (s, w) => `.text-${s}-${w}`,
      tracking: t.tracking?.text || {},
      lineHeight: (s) => t.fontSize[s]?.[1].lineHeight,
    },
    {
      className: (s, w) => `.text-p-${s}-${w}`,
      tracking: t.tracking?.paragraph || {},
      lineHeight: (s) => t.paragraph?.[s]?.lineHeight,
    },
  ]
  for (const group of groups) {
    for (const [size, byWeight] of Object.entries(group.tracking)) {
      const entry = t.fontSize[size]
      if (!entry) continue
      const [fontSizePx] = entry
      const lhRatio = group.lineHeight(size)
      const transform = t.textTransform?.[size]
      for (const weight of WEIGHT_VARIANTS) {
        if (!(weight in byWeight)) continue
        out[group.className(size, weight)] = {
          fontSize: scaleFontSize(fontSizePx),
          lineHeight: fixedLineHeightPx(fontSizePx, lhRatio),
          fontWeight: String(t.fontWeight[weight]),
          letterSpacing: byWeight[weight],
          ...(transform ? { textTransform: transform } : {}),
        }
      }
    }
  }
  for (const [size, transform] of Object.entries(t.textTransform || {})) {
    out[`.text-${size}`] = {
      ...(out[`.text-${size}`] || {}),
      textTransform: transform,
    }
  }
  return out
}

export default plugin(
  function ({ addComponents, addBase }) {
    addBase({
      ':root': {
        '--font-scale': '1',
        '--prose-font-size': `calc(15px * ${SCALE_VAR})`,
      },
    })
    addComponents(buildScaledTextStyleUtilities())
  },
  {
    theme: {
      fontSize: buildScaledFontSize(),
    },
  },
)
