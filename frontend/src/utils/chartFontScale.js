/**
 * Scale fontSize values in ECharts option trees. Line heights and grid layout
 * stay unchanged so chart dimensions are not affected.
 */
export function scaleChartOptions(options, scale) {
  const s = parseFloat(scale)
  if (!options || Number.isNaN(s) || s === 1) return options
  return walk(options, s)
}

function walk(value, scale) {
  if (Array.isArray(value)) {
    return value.map((item) => walk(item, scale))
  }
  if (value && typeof value === 'object') {
    const out = {}
    for (const [key, child] of Object.entries(value)) {
      if (key === 'fontSize' && typeof child === 'number') {
        out[key] = Math.round(child * scale * 10) / 10
      } else {
        out[key] = walk(child, scale)
      }
    }
    return out
  }
  return value
}
