<template>
  <div class="flex gap-2">
    <button
      v-for="option in FONT_SCALE_OPTIONS"
      :key="option.value"
      type="button"
      class="flex-1 rounded-lg border px-3 py-2.5 text-left transition-colors"
      :class="
        currentFontScale === option.value
          ? 'border-outline-gray-7 bg-surface-gray-2'
          : 'border-outline-elevation-2 hover:bg-surface-gray-1'
      "
      @click="setFontScale(option.value)"
    >
      <div class="text-base-medium text-ink-gray-8">
        {{ __(option.label) }}
      </div>
      <div class="text-p-sm text-ink-gray-5 mt-0.5">
        {{ option.description }}
      </div>
    </button>
  </div>
</template>

<script setup>
import { useFontScale } from '@/composables/useFontScale'

const { currentFontScale, setFontScale, FONT_SCALE_OPTIONS } = useFontScale()
</script>
