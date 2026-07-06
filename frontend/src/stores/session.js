import { defineStore } from 'pinia'
import { createResource, call } from 'frappe-ui'
import router from '@/router'
import { ref, computed } from 'vue'
import { usersStore } from '@/stores/users'

export const sessionStore = defineStore('crm-session', () => {
  function sessionUser() {
    let cookies = new URLSearchParams(document.cookie.split('; ').join('&'))
    let _sessionUser = cookies.get('user_id')
    if (_sessionUser) {
      try {
        _sessionUser = decodeURIComponent(_sessionUser)
      } catch {
        // keep raw cookie value
      }
    }
    if (_sessionUser === 'Guest') {
      _sessionUser = null
    }
    return _sessionUser
  }

  let user = ref(sessionUser())
  const isLoggedIn = computed(() => !!user.value)

  const login = createResource({
    url: 'login',
    onError() {
      throw new Error(__('Invalid Email or Password'))
    },
    onSuccess() {
      user.value = sessionUser()
      login.reset()
      router.replace({ path: '/' })
    },
  })

  async function loginWithTripAI({ login_id, password }) {
    const result = await call('crm.api.tripai.login', { login_id, password })
    user.value = result?.user || sessionUser()
    if (!user.value) {
      throw new Error(__('Login failed'))
    }
    // Guest-time users fetch fails; refresh CRM user list after TripAI login.
    const { users } = usersStore()
    await users.reload()
    return result
  }

  const logout = createResource({
    url: 'logout',
    onSuccess() {
      user.value = null
      window.location.href = '/crm/login'
    },
  })

  return {
    user,
    isLoggedIn,
    login,
    loginWithTripAI,
    logout,
  }
})
