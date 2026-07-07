import './index.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createDialog } from './utils/dialogs'
import { initSocket } from './socket'
import router from './router'
import translationPlugin from './translation'
import App from './App.vue'
import { initializeFontScale } from '@/composables/useFontScale'
import { loadTranslations } from '@/utils/loadTranslations'

import {
  FrappeUI,
  Button,
  Input,
  TextInput,
  FormControl,
  ErrorMessage,
  Dialog,
  Alert,
  Badge,
  setConfig,
  frappeRequest,
  FeatherIcon,
} from 'frappe-ui'

import { telemetryPlugin } from 'frappe-ui/frappe'

let globalComponents = {
  Button,
  TextInput,
  Input,
  FormControl,
  ErrorMessage,
  Dialog,
  Alert,
  Badge,
  FeatherIcon,
}

// create a pinia instance
let pinia = createPinia()

let app = createApp(App)

setConfig('resourceFetcher', frappeRequest)
// CRM owns socket setup in ./socket.js — disable frappe-ui default (port 9000).
app.use(FrappeUI, { socketio: false })
app.use(pinia)
app.use(router)
app.use(translationPlugin)
for (let key in globalComponents) {
  app.component(key, globalComponents[key])
}
app.use(telemetryPlugin, { app_name: 'crm' })

initializeFontScale()

app.config.globalProperties.$dialog = createDialog

async function bootstrap() {
  setConfig('translatedMessages', window.translated_messages || {})

  if (import.meta.env.DEV) {
    const values = await frappeRequest({
      url: '/api/method/crm.www.crm.get_context_for_dev',
    })
    for (let key in values) {
      window[key] = values[key]
    }
    setConfig('translatedMessages', window.translated_messages || {})
  }

  await loadTranslations()

  const socket = initSocket()
  app.config.globalProperties.$socket = socket
  app.mount('#app')
}

bootstrap()

if (import.meta.env.DEV) {
  window.$dialog = createDialog
}
