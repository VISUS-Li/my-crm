<template>
  <button
    type="button"
    class="flex cursor-pointer flex-col gap-1 rounded-xl border p-4 text-left transition-colors hover:border-outline-brand hover:bg-surface-brand-1"
    @click="$emit('click')"
  >
    <div class="flex items-center justify-between">
      <span class="text-p-sm text-ink-gray-6">{{ label }}</span>
      <span
        class="grid size-8 place-items-center rounded-full"
        :class="iconBgClass"
      >
        <component :is="iconComponent" class="size-4" :class="iconClass" />
      </span>
    </div>
    <div class="text-3xl-semibold text-ink-gray-9">{{ value }}</div>
  </button>
</template>

<script setup>
import LucidePhone from '~icons/lucide/phone'
import LucideCheck from '~icons/lucide/check'
import LucideStar from '~icons/lucide/star'
import LucideMapPin from '~icons/lucide/map-pin'
import { computed } from 'vue'

const props = defineProps({
  label: { type: String, required: true },
  value: { type: [Number, String], default: 0 },
  theme: { type: String, default: 'blue' },
  icon: { type: String, default: 'phone' },
})

defineEmits(['click'])

const themeMap = {
  orange: {
    bg: 'bg-surface-orange-1',
    icon: 'text-ink-orange-3',
  },
  cyan: {
    bg: 'bg-surface-cyan-1',
    icon: 'text-ink-cyan-3',
  },
  green: {
    bg: 'bg-surface-green-1',
    icon: 'text-ink-green-3',
  },
  blue: {
    bg: 'bg-surface-blue-1',
    icon: 'text-ink-blue-3',
  },
}

const iconMap = {
  phone: LucidePhone,
  check: LucideCheck,
  star: LucideStar,
  'map-pin': LucideMapPin,
}

const iconBgClass = computed(() => themeMap[props.theme]?.bg || themeMap.blue.bg)
const iconClass = computed(() => themeMap[props.theme]?.icon || themeMap.blue.icon)
const iconComponent = computed(() => iconMap[props.icon] || LucidePhone)
</script>
