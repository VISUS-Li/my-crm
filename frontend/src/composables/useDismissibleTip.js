import { computed, ref } from 'vue'

const STORAGE_PREFIX = 'dismissibleTip:'

function readDismissed(key) {
  try {
    return localStorage.getItem(`${STORAGE_PREFIX}${key}`) === '1'
  } catch {
    return false
  }
}

function writeDismissed(key) {
  try {
    localStorage.setItem(`${STORAGE_PREFIX}${key}`, '1')
  } catch {
    // ignore storage failures in restricted environments
  }
}

export function useDismissibleTip(key) {
  if (!key) {
    return {
      visible: computed(() => true),
      dismiss: () => {},
    }
  }

  const dismissed = ref(readDismissed(key))

  return {
    visible: computed(() => !dismissed.value),
    dismiss: () => {
      if (dismissed.value) return
      dismissed.value = true
      writeDismissed(key)
    },
  }
}
