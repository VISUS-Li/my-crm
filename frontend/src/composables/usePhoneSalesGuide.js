import { computed, ref } from 'vue'
import { getGuideById } from '@/config/phoneSalesGuides'

export const showGuideModal = ref(false)
export const activeGuideId = ref(null)

export function openPhoneSalesGuide(id) {
  activeGuideId.value = id
  showGuideModal.value = true
}

export function closePhoneSalesGuide() {
  showGuideModal.value = false
}

export function usePhoneSalesGuide() {
  const activeGuide = computed(() => getGuideById(activeGuideId.value))

  return {
    showGuideModal,
    activeGuideId,
    activeGuide,
    openPhoneSalesGuide,
    closePhoneSalesGuide,
  }
}
