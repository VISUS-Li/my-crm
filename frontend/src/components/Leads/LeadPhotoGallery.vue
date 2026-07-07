<template>
  <div v-if="photos.length" class="lead-photo-gallery">
    <div class="mb-2 text-p-sm font-medium text-ink-gray-7">
      {{ title || __('Photos') }}
      <span v-if="photos.length > 1" class="font-normal text-ink-gray-5">
        ({{ photos.length }})
      </span>
    </div>
    <div class="flex flex-wrap gap-2">
      <button
        v-for="(photo, index) in photos"
        :key="`${photo.url}-${index}`"
        type="button"
        class="group relative size-16 overflow-hidden rounded-lg border border-outline-gray-2 bg-surface-gray-1 transition hover:border-outline-gray-3 hover:shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ink-blue-3 sm:size-20"
        :title="photo.title || __('View photo')"
        @click="openPreview(index)"
      >
        <img
          :src="photo.url"
          :alt="photo.title || __('Lead photo')"
          class="size-full object-cover transition group-hover:scale-105"
          loading="lazy"
        />
      </button>
    </div>

    <Dialog
      v-model:open="previewOpen"
      :title="activePhoto?.title || __('Photo')"
      size="5xl"
    >
      <template #default>
        <div class="flex flex-col gap-3">
          <div
            class="flex max-h-[70vh] min-h-[240px] items-center justify-center overflow-hidden rounded-lg bg-surface-gray-1"
          >
            <img
              v-if="activePhoto"
              :src="activePhoto.url"
              :alt="activePhoto.title || __('Lead photo')"
              class="max-h-[70vh] max-w-full object-contain"
            />
          </div>
          <div
            v-if="photos.length > 1"
            class="flex items-center justify-between gap-3"
          >
            <Button
              variant="outline"
              :label="__('Previous')"
              :disabled="activeIndex <= 0"
              @click="showPrevious"
            />
            <span class="text-p-sm text-ink-gray-6">
              {{ activeIndex + 1 }} / {{ photos.length }}
            </span>
            <Button
              variant="outline"
              :label="__('Next')"
              :disabled="activeIndex >= photos.length - 1"
              @click="showNext"
            />
          </div>
        </div>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { Button, Dialog } from 'frappe-ui'

const props = defineProps({
  photos: { type: Array, default: () => [] },
  title: { type: String, default: '' },
})

const previewOpen = ref(false)
const activeIndex = ref(0)

const activePhoto = computed(() => props.photos[activeIndex.value] || null)

function openPreview(index) {
  activeIndex.value = index
  previewOpen.value = true
}

function showPrevious() {
  if (activeIndex.value > 0) activeIndex.value -= 1
}

function showNext() {
  if (activeIndex.value < props.photos.length - 1) activeIndex.value += 1
}
</script>
