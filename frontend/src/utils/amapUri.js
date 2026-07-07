/**
 * Build / open Amap marker URIs (free — no API key, no quota).
 * @see https://lbs.amap.com/api/uri-api
 */

export function parsePoiLocation(value) {
  if (!value) return null
  try {
    const geo = JSON.parse(value)
    const features = geo.type === 'FeatureCollection' ? geo.features : [geo]
    const point = features.find((f) => f.geometry?.type === 'Point')
    if (!point) return null
    const [lng, lat] = point.geometry.coordinates
    if (lng == null || lat == null || Number.isNaN(lng) || Number.isNaN(lat)) {
      return null
    }
    return { lng, lat }
  } catch {
    return null
  }
}

export function buildAmapMarkerUri({
  lng,
  lat,
  name,
  poiId,
  src = 'crm',
} = {}) {
  if (poiId) {
    const params = new URLSearchParams({ poiid: poiId, src, callnative: '1' })
    return `https://uri.amap.com/marker?${params.toString()}`
  }
  if (lng != null && lat != null) {
    const params = new URLSearchParams({
      position: `${lng},${lat}`,
      coordinate: 'gaode',
      src,
      callnative: '1',
    })
    if (name) params.set('name', name)
    return `https://uri.amap.com/marker?${params.toString()}`
  }
  return null
}

export function getAmapMarkerUri({ address, location, poiId, name, district } = {}) {
  const coords = parsePoiLocation(location)
  return buildAmapMarkerUri({
    lng: coords?.lng,
    lat: coords?.lat,
    name: name || address || district,
    poiId,
  })
}

export function openAmapMarker(options) {
  const url = getAmapMarkerUri(options)
  if (url) window.open(url, '_blank', 'noopener,noreferrer')
  return Boolean(url)
}

export function getPoiDisplayAddress(address, district) {
  const text = (address || '').trim()
  if (text) return text
  return (district || '').trim()
}

export function canOpenAmapMarker({ location, poiId } = {}) {
  return Boolean(poiId || parsePoiLocation(location))
}
