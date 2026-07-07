<template>
  <div class="flex min-h-screen items-center justify-center bg-surface-gray-1 px-4 text-p-base">
    <div class="w-full max-w-sm rounded-xl border bg-surface-white p-6 shadow-sm">
      <div class="mb-6 text-center">
        <h1 class="text-xl-semibold text-ink-gray-9">{{ __('Sign in to TripAI CRM') }}</h1>
        <p class="mt-1 text-p-sm text-ink-gray-6">
          {{ __('Use your TripAI phone number or email') }}
        </p>
      </div>

      <form class="space-y-4" @submit.prevent="submitLogin">
        <FormControl
          v-model="loginId"
          type="text"
          :label="__('Phone or Email')"
          :placeholder="__('e.g. 13800138000 or name@example.com')"
          autocomplete="username"
          required
        />
        <FormControl
          v-model="password"
          type="password"
          :label="__('Password')"
          autocomplete="current-password"
          required
        />
        <Button
          type="submit"
          variant="solid"
          class="w-full"
          :label="__('Sign in')"
          :loading="loading"
        />
      </form>

      <p v-if="error" class="mt-4 text-center text-p-sm text-red-600">{{ error }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Button, FormControl } from 'frappe-ui'
import { sessionStore } from '@/stores/session'

const route = useRoute()
const router = useRouter()
const { loginWithTripAI } = sessionStore()

const loginId = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

async function submitLogin() {
  error.value = ''
  loading.value = true
  try {
    await loginWithTripAI({
      login_id: loginId.value.trim(),
      password: password.value,
    })
    const redirect = route.query.redirect || '/'
    router.replace(typeof redirect === 'string' ? redirect : '/')
  } catch (err) {
    error.value =
      err?.messages?.[0] || err?.message || __('Invalid phone, email, or password')
  } finally {
    loading.value = false
  }
}
</script>
