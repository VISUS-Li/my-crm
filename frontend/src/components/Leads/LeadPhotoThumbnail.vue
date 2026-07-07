<template>
  <img
    v-if="src"
    :src="src"
    :alt="alt || __('Lead photo')"
    :class="[
      'rounded-md border border-outline-gray-2 object-cover bg-surface-gray-1 flex-shrink-0',
      sizeClass,
    ]"
    loading="lazy"
  />
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  src: { type: String, default: '' },
  alt: { type: String, default: '' },
  size: { type: String, default: 'sm' },
})

const sizeClass = computed(() => {
  if (props.size === 'md') return 'size-10'
  if (props.size === 'lg') return 'size-12'
  return 'size-9'
})
</script>
