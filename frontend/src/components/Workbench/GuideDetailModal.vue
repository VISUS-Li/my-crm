<template>
  <Dialog
    v-model:open="showGuideModal"
    :size="'3xl'"
    @close="closePhoneSalesGuide"
  >
    <template #body>
      <div v-if="activeGuide" class="flex max-h-[calc(100vh-8rem)] flex-col">
        <div class="border-b px-6 py-5">
          <div class="flex items-start gap-3">
            <div
              class="grid size-10 shrink-0 place-items-center rounded-lg bg-surface-brand-1"
            >
              <component
                :is="iconComponent"
                class="size-5 text-ink-brand-3"
              />
            </div>
            <div>
              <h2 class="text-xl-semibold text-ink-gray-9">
                {{ __(activeGuide.title) }}
              </h2>
              <p class="mt-1 text-p-base text-ink-gray-6">
                {{ __(activeGuide.summary) }}
              </p>
            </div>
          </div>
        </div>

        <div class="flex-1 overflow-y-auto px-6 py-5">
          <ol class="space-y-5">
            <li
              v-for="(step, index) in activeGuide.steps"
              :key="index"
              class="flex gap-4"
            >
              <div
                class="flex size-7 shrink-0 items-center justify-center rounded-full bg-surface-brand-1 text-p-sm-medium text-ink-brand-3"
              >
                {{ index + 1 }}
              </div>
              <div class="min-w-0 flex-1">
                <div class="text-p-base-medium text-ink-gray-9">
                  {{ __(step.title) }}
                </div>
                <p class="mt-1 text-p-base text-ink-gray-7">
                  {{ __(step.body) }}
                </p>
                <div
                  v-if="step.tip"
                  class="mt-2 flex gap-2 rounded-lg border border-outline-brand bg-surface-brand-1 px-3 py-2 text-p-sm text-ink-gray-7"
                >
                  <LucideInfo class="mt-0.5 size-4 shrink-0 text-ink-brand-3" />
                  <span>{{ __(step.tip) }}</span>
                </div>
              </div>
            </li>
          </ol>
        </div>

        <div
          class="flex flex-wrap gap-2 border-t bg-surface-gray-1 px-6 py-4"
        >
          <Button
            v-for="(action, index) in activeGuide.actions"
            :key="index"
            :variant="index === 0 ? 'solid' : 'outline'"
            :label="__(action.label)"
            @click="runAction(action)"
          />
          <Button
            variant="ghost"
            :label="__('Close')"
            class="ml-auto"
            @click="closePhoneSalesGuide"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import LucideInfo from '~icons/lucide/info'
import LucideUtensils from '~icons/lucide/utensils'
import LucideSettings from '~icons/lucide/settings'
import LucidePhone from '~icons/lucide/phone'
import LucideClipboard from '~icons/lucide/clipboard-list'
import LucideStar from '~icons/lucide/star'
import LucideMapPin from '~icons/lucide/map-pin'
import {
  showSettings,
  activeSettingsPage,
} from '@/composables/settings'
import { usePhoneSalesGuide } from '@/composables/usePhoneSalesGuide'
import { Dialog, Button } from 'frappe-ui'
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const { showGuideModal, activeGuide, closePhoneSalesGuide } = usePhoneSalesGuide()

const iconMap = {
  utensils: LucideUtensils,
  settings: LucideSettings,
  phone: LucidePhone,
  clipboard: LucideClipboard,
  star: LucideStar,
  'map-pin': LucideMapPin,
}

const iconComponent = computed(() => {
  const key = activeGuide.value?.icon
  return iconMap[key] || LucideMapPin
})

function runAction(action) {
  closePhoneSalesGuide()
  if (action.type === 'route' && action.to) {
    router.push(action.to)
    return
  }
  if (action.type === 'settings' && action.page) {
    showSettings.value = true
    activeSettingsPage.value = action.page
  }
}
</script>
