<template>
  <FrappeUIProvider>
    <NotPermitted v-if="$route.name === 'Not Permitted'" />
    <router-view v-else-if="isPublicRoute" :key="$route.fullPath" />
    <Layout v-else-if="session.isLoggedIn" class="isolate">
      <router-view :key="$route.fullPath" />
    </Layout>
    <Dialogs />
    <DoctypeModals />
    <EventNotificationPopup />
  </FrappeUIProvider>
</template>

<script setup>
import NotPermitted from '@/pages/NotPermitted.vue'
import EventNotificationPopup from '@/components/EventNotificationPopup.vue'
import DoctypeModals from '@/components/Modals/DoctypeModals.vue'
import { Dialogs } from '@/utils/dialogs'
import { sessionStore } from '@/stores/session'
import { FrappeUIProvider, setConfig, useTheme } from 'frappe-ui'
import { computed, defineAsyncComponent, provide } from 'vue'
import { useRoute } from 'vue-router'
import { useFontScale } from '@/composables/useFontScale'
import { getMergedTranslations } from '@/utils/loadTranslations'

const session = sessionStore()
const route = useRoute()
provide('session', session)

const PUBLIC_ROUTE_NAMES = ['Login', 'Welcome']
const isPublicRoute = computed(() => PUBLIC_ROUTE_NAMES.includes(route.name))

const { setTheme } = useTheme()
if (!localStorage.getItem('theme')) {
  setTheme('light')
}

useFontScale()

const MobileLayout = defineAsyncComponent(
  () => import('./components/Layouts/MobileLayout.vue'),
)
const DesktopLayout = defineAsyncComponent(
  () => import('./components/Layouts/DesktopLayout.vue'),
)
const Layout = computed(() => {
  if (window.innerWidth < 640) {
    return MobileLayout
  } else {
    return DesktopLayout
  }
})

setConfig('systemTimezone', window.timezone?.system || null)
setConfig('localTimezone', window.timezone?.user || null)
setConfig(
  'translatedMessages',
  getMergedTranslations(window.translated_messages || {}),
)
</script>
