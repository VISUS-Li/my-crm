<template>
  <div class="flex h-screen items-center justify-center bg-surface-gray-1">
    <div class="text-center">
      <LoadingIndicator v-if="loading" class="mx-auto h-8 w-8 text-ink-gray-6" />
      <div v-else-if="error" class="max-w-md px-4">
        <h2 class="text-lg font-medium text-ink-gray-9">{{ __('Authentication Failed') }}</h2>
        <p class="mt-2 text-p-sm text-ink-gray-6">{{ error }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { createResource, LoadingIndicator } from 'frappe-ui'
import { sessionStore } from '@/stores/session'

const route = useRoute()
const router = useRouter()
const { user } = sessionStore()
const loading = ref(true)
const error = ref('')

const exchange = createResource({
  url: 'crm.api.tripai.exchange_launch_ticket',
  onSuccess(data) {
    user.value = data.user
    const redirect = data.redirect_to || '/crm'
    if (redirect.startsWith('http')) {
      window.location.href = redirect
      return
    }
    router.replace(redirect.replace(/^\/crm/, '') || '/')
  },
  onError(err) {
    loading.value = false
    error.value =
      err?.messages?.[0] || err?.message || __('Unable to complete TripAI login')
  },
})

onMounted(() => {
  const ticket = route.query.ticket
  const projectKey = route.query.projectKey
  if (!ticket) {
    loading.value = false
    error.value = __('Missing launch ticket')
    return
  }
  exchange.submit({ ticket, project_key: projectKey })
})
</script>
