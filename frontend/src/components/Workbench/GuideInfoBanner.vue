<template>
  <div
    class="mb-4 flex items-start gap-3 rounded-xl border border-outline-brand bg-surface-brand-1 px-4 py-3"
  >
    <LucideInfo class="mt-0.5 size-4 shrink-0 text-ink-brand-3" />
    <div class="min-w-0 flex-1">
      <div class="text-p-base-medium text-ink-gray-9">{{ title }}</div>
      <p class="mt-0.5 text-p-sm text-ink-gray-7">{{ description }}</p>
      <Button
        v-if="guideId"
        variant="ghost"
        size="sm"
        class="mt-2 !px-0"
        :label="__('View detailed guide')"
        icon-left="book-open"
        @click="openPhoneSalesGuide(guideId)"
      />
    </div>
  </div>
</template>

<script setup>
import LucideInfo from '~icons/lucide/info'
import { openPhoneSalesGuide } from '@/composables/usePhoneSalesGuide'
import { Button } from 'frappe-ui'

defineProps({
  title: { type: String, required: true },
  description: { type: String, required: true },
  guideId: { type: String, default: '' },
})
</script>
