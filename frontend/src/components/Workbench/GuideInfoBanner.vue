<template>
  <div
    class="guide-banner mb-4 flex items-start gap-3.5 rounded-xl border border-outline-brand bg-gradient-to-r from-surface-brand-1 to-white px-4 py-3.5 shadow-sm"
  >
    <div
      class="grid size-9 shrink-0 place-items-center rounded-lg bg-white shadow-sm ring-1 ring-outline-brand"
    >
      <LucideSparkles class="size-4 text-ink-brand-3" />
    </div>
    <div class="min-w-0 flex-1">
      <div class="text-p-base-semibold text-ink-gray-9">{{ title }}</div>
      <p class="mt-1 text-p-sm leading-relaxed text-ink-gray-7">
        {{ description }}
      </p>
      <Button
        v-if="guideId"
        variant="ghost"
        size="sm"
        class="mt-2 !px-0 text-ink-brand-3 hover:!bg-transparent"
        :label="__('View detailed guide')"
        icon-left="book-open"
        @click="openPhoneSalesGuide(guideId)"
      />
    </div>
  </div>
</template>

<script setup>
import LucideSparkles from '~icons/lucide/sparkles'
import { openPhoneSalesGuide } from '@/composables/usePhoneSalesGuide'
import { Button } from 'frappe-ui'

defineProps({
  title: { type: String, required: true },
  description: { type: String, required: true },
  guideId: { type: String, default: '' },
})
</script>

<style scoped>
.guide-banner {
  border-left-width: 4px;
  border-left-color: var(--ink-brand-3, #3538cd);
}
</style>
