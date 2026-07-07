/** Parse / join delimited preset values for Amap POI sync jobs. */

export const POI_VALUE_DELIMITER = '|'

export function parseDelimitedValues(value) {
  if (!value || typeof value !== 'string') return []
  return value
    .split(POI_VALUE_DELIMITER)
    .map((item) => item.trim())
    .filter(Boolean)
}

export function joinDelimitedValues(values) {
  const unique = [...new Set((values || []).map((item) => String(item).trim()).filter(Boolean))]
  return unique.join(POI_VALUE_DELIMITER)
}

export function normalizeOptionGroups(groups) {
  return (groups || []).map((group) => {
    const items = (group.items || []).map((item) =>
      typeof item === 'string' ? { label: item, value: item } : item,
    )
    return {
      group: group.group,
      categoryValue: group.categoryValue || group.categoryKeyword || '',
      items,
    }
  })
}

export function flattenOptionGroups(groups) {
  return normalizeOptionGroups(groups).flatMap((group) => group.items)
}

export function findOptionLabel(groups, value) {
  for (const group of normalizeOptionGroups(groups)) {
    if (group.categoryValue === value) {
      return group.group
    }
    const match = group.items.find((item) => item.value === value)
    if (match) return match.label
  }
  return value
}

export function filterOptionGroups(groups, query) {
  const q = (query || '').trim().toLowerCase()
  if (!q) return normalizeOptionGroups(groups)

  return normalizeOptionGroups(groups)
    .map((group) => {
      const groupLabel = group.group.toLowerCase()
      const categoryMatches =
        group.categoryValue && group.categoryValue.toLowerCase().includes(q)

      const matchedItems = group.items.filter((item) => {
        const label = String(item.label || '').toLowerCase()
        const val = String(item.value || '').toLowerCase()
        return label.includes(q) || val.includes(q) || groupLabel.includes(q)
      })

      if (!categoryMatches && matchedItems.length === 0) return null

      return {
        ...group,
        items: categoryMatches ? group.items : matchedItems,
      }
    })
    .filter(Boolean)
}

export function isPresetValue(groups, value) {
  for (const group of normalizeOptionGroups(groups)) {
    if (group.categoryValue === value) return true
    if (group.items.some((item) => item.value === value)) return true
  }
  return false
}
