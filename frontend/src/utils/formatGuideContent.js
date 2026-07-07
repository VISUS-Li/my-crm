/**
 * Split guide body text into segments for highlighted rendering.
 * Paths (A → B → C) and quoted terms ("...") are styled in the UI.
 */
export function parseGuideBody(body) {
  if (!body) return [{ type: 'text', value: '' }]

  const segments = []
  const pattern = /"([^"]+)"|([^"→\n]+(?:→[^"→\n]+)+)/g
  let lastIndex = 0
  let match

  while ((match = pattern.exec(body)) !== null) {
    if (match.index > lastIndex) {
      segments.push({ type: 'text', value: body.slice(lastIndex, match.index) })
    }
    if (match[1] !== undefined) {
      segments.push({ type: 'quote', value: match[1] })
    } else {
      segments.push({ type: 'path', value: match[2].trim() })
    }
    lastIndex = match.index + match[0].length
  }

  if (lastIndex < body.length) {
    segments.push({ type: 'text', value: body.slice(lastIndex) })
  }

  return segments.length ? segments : [{ type: 'text', value: body }]
}
