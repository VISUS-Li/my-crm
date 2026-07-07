<template>
  <section :id="sectionId" class="mb-6">
    <div class="mb-3 flex items-center justify-between gap-3">
      <div>
        <h2 class="text-lg-semibold text-ink-gray-9">
          {{ __('Operation Guides') }}
        </h2>
        <p class="mt-0.5 text-p-sm text-ink-gray-6">
          {{
            __(
              'Choose a scenario to see step-by-step instructions for your daily work.',
            )
          }}
        </p>
      </div>
      <Button
        v-if="compact"
        variant="ghost"
        :label="__('View all on Workbench')"
        @click="router.push({ name: 'Workbench', hash: '#operation-guides' })"
      />
    </div>

    <div class="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
      <article
        v-for="guide in guides"
        :key="guide.id"
        class="flex flex-col rounded-xl border bg-surface-elevation-2 p-4 transition-colors hover:border-outline-brand"
      >
        <div class="flex items-start gap-3">
          <div
            class="grid size-9 shrink-0 place-items-center rounded-lg bg-surface-gray-2"
          >
            <component
              :is="getIcon(guide.icon)"
              class="size-4 text-ink-gray-7"
            />
          </div>
          <div class="min-w-0 flex-1">
            <h3 class="text-p-base-medium text-ink-gray-9">
              {{ __(guide.title) }}
            </h3>
            <p class="mt-1 line-clamp-2 text-p-sm text-ink-gray-6">
              {{ __(guide.summary) }}
            </p>
          </div>
        </div>
        <div class="mt-4 flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            :label="__('View detailed guide')"
            icon-left="book-open"
            @click="openPhoneSalesGuide(guide.id)"
          />
          <span
            v-if="guide.id === highlightGuideId"
            class="rounded-full bg-surface-brand-1 px-2 py-0.5 text-p-xs-medium text-ink-brand-3"
          >
            {{ __('Recommended') }}
          </span>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup>
import LucideUtensils from '~icons/lucide/utensils'
import LucideSettings from '~icons/lucide/settings'
import LucidePhone from '~icons/lucide/phone'
import LucideClipboard from '~icons/lucide/clipboard-list'
import LucideStar from '~icons/lucide/star'
import LucideMapPin from '~icons/lucide/map-pin'
import { getGuideList } from '@/config/phoneSalesGuides'
import { openPhoneSalesGuide } from '@/composables/usePhoneSalesGuide'
import { Button } from 'frappe-ui'
import { useRouter } from 'vue-router'

defineProps({
  compact: { type: Boolean, default: false },
  highlightGuideId: { type: String, default: '' },
  sectionId: { type: String, default: 'operation-guides' },
})

const router = useRouter()
const guides = getGuideList({ audience: 'user' })

const iconMap = {
  utensils: LucideUtensils,
  settings: LucideSettings,
  phone: LucidePhone,
  clipboard: LucideClipboard,
  star: LucideStar,
  'map-pin': LucideMapPin,
}

function getIcon(name) {
  return iconMap[name] || LucideMapPin
}
</script>
