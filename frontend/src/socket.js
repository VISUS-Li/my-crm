import { io } from 'socket.io-client'
import { getCachedListResource, getCachedResource } from 'frappe-ui'

const DEFAULT_SOCKETIO_PORT = 9010

function getSocketPort() {
  const port = window.socketio_port
  if (port == null || port === '') return DEFAULT_SOCKETIO_PORT
  const parsed = Number(port)
  return Number.isFinite(parsed) ? parsed : DEFAULT_SOCKETIO_PORT
}

export function getSocketUrl() {
  const host = window.location.hostname
  const siteName = window.site_name || host
  const webPort = window.location.port
  const socketPort = getSocketPort()

  // Standard web ports go through the same origin (reverse proxy routes /socket.io/).
  const useSameOrigin = !webPort || webPort === '80' || webPort === '443'

  let origin
  if (useSameOrigin) {
    origin = window.location.origin
  } else {
    const protocol = window.location.protocol === 'https:' ? 'https' : 'http'
    origin = `${protocol}//${host}:${socketPort}`
  }

  return `${origin}/${siteName}`
}

export function initSocket() {
  const socket = io(getSocketUrl(), {
    path: '/socket.io/',
    withCredentials: true,
    reconnectionAttempts: 5,
  })
  socket.on('refetch_resource', (data) => {
    if (data.cache_key) {
      let resource =
        getCachedResource(data.cache_key) ||
        getCachedListResource(data.cache_key)
      if (resource) {
        resource.reload()
      }
    }
  })
  return socket
}
