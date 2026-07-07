<template>
  <Dialog
    v-model:open="showGuideModal"
    :size="'3xl'"
    @close="closePhoneSalesGuide"
  >
    <template #body>
      <div v-if="activeGuide" class="flex max-h-[calc(100vh-8rem)] flex-col">
        <div class="border-b bg-gradient-to-r from-surface-brand-1 to-surface-gray-1 px-6 py-5">
          <div class="flex items-start gap-4">
            <div
              class="grid size-12 shrink-0 place-items-center rounded-xl bg-white shadow-sm ring-1 ring-outline-brand"
            >
              <component
                :is="iconComponent"
                class="size-6 text-ink-brand-3"
              />
            </div>
            <div class="min-w-0 flex-1">
              <div class="flex flex-wrap items-center gap-2">
                <h2 class="text-xl-semibold text-ink-gray-9">
                  {{ __(activeGuide.title) }}
                </h2>
                <span
                  v-if="activeGuide.audience === 'admin'"
                  class="rounded-full bg-amber-100 px-2.5 py-0.5 text-p-xs-medium text-amber-800"
                >
                  {{ __('Admin only') }}
                </span>
              </div>
              <p class="mt-1.5 text-p-base leading-relaxed text-ink-gray-7">
                {{ __(activeGuide.summary) }}
              </p>
            </div>
          </div>
        </div>

        <div class="flex-1 overflow-y-auto px-6 py-5">
          <ol class="relative space-y-4">
            <li
              v-for="(step, index) in activeGuide.steps"
              :key="index"
              class="relative pl-0"
            >
              <div
                v-if="index < activeGuide.steps.length - 1"
                class="guide-step-line"
              />
              <div
                class="relative flex gap-4 rounded-xl border border-outline-gray-2 bg-surface-elevation-2 p-4 shadow-sm"
              >
                <div
                  class="flex size-8 shrink-0 items-center justify-center rounded-full bg-ink-brand-3 text-p-sm-semibold text-white shadow-sm"
                >
                  {{ index + 1 }}
                </div>
                <div class="min-w-0 flex-1">
                  <div class="text-p-base-semibold text-ink-gray-9">
                    {{ __(step.title) }}
                  </div>
                  <p class="mt-2 text-p-base leading-relaxed text-ink-gray-7">
                    <template
                      v-for="(segment, segIndex) in parseStepBody(step.body)"
                      :key="segIndex"
                    >
                      <span v-if="segment.type === 'text'">{{
                        segment.value
                      }}</span>
                      <span
                        v-else-if="segment.type === 'path'"
                        class="guide-path"
                      >
                        {{ segment.value }}
                      </span>
                      <span
                        v-else-if="segment.type === 'quote'"
                        class="guide-quote"
                      >
                        “{{ segment.value }}”
                      </span>
                    </template>
                  </p>
                  <div
                    v-if="step.keywords?.length"
                    class="mt-2.5 flex flex-wrap gap-1.5"
                  >
                    <span
                      v-for="keyword in step.keywords"
                      :key="keyword"
                      class="guide-keyword"
                    >
                      {{ keyword }}
                    </span>
                  </div>
                  <div
                    v-if="step.tip"
                    class="mt-3 flex gap-2.5 rounded-lg border border-amber-200 bg-amber-50 px-3.5 py-2.5"
                  >
                    <LucideLightbulb
                      class="mt-0.5 size-4 shrink-0 text-amber-600"
                    />
                    <span class="text-p-sm leading-relaxed text-amber-900">{{
                      __(step.tip)
                    }}</span>
                  </div>
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
import LucideLightbulb from '~icons/lucide/lightbulb'
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
import { parseGuideBody } from '@/utils/formatGuideContent'
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

function parseStepBody(body) {
  return parseGuideBody(__(body))
}

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

<style scoped>
.guide-step-line {
  position: absolute;
  left: 1.25rem;
  top: 2.75rem;
  bottom: -1rem;
  width: 2px;
  background: linear-gradient(
    to bottom,
    var(--outline-brand, #c7d7fe) 0%,
    var(--outline-gray-2, #e5e7eb) 100%
  );
}

.guide-path {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.125rem;
  margin: 0 0.125rem;
  padding: 0.125rem 0.5rem;
  border-radius: 0.375rem;
  background: var(--surface-brand-1, #eff4ff);
  color: var(--ink-brand-3, #3538cd);
  font-weight: 500;
  font-size: 0.875rem;
  line-height: 1.25rem;
}

.guide-quote {
  display: inline;
  margin: 0 0.125rem;
  padding: 0.0625rem 0.375rem;
  border-radius: 0.25rem;
  background: var(--surface-gray-2, #f3f4f6);
  color: var(--ink-gray-9, #111827);
  font-weight: 500;
}

.guide-keyword {
  display: inline-flex;
  padding: 0.125rem 0.625rem;
  border-radius: 9999px;
  border: 1px solid var(--outline-brand, #c7d7fe);
  background: white;
  color: var(--ink-brand-3, #3538cd);
  font-size: 0.8125rem;
  font-weight: 500;
}
</style>
