<template>
  <div class="flex min-w-0 flex-col gap-1">
    <div
      v-if="readOnly || !editable"
      class="flex min-w-0 items-start gap-1.5"
    >
      <span
        v-if="canOpen"
        class="lucide-map-pin mt-0.5 size-4 shrink-0 text-blue-600 dark:text-blue-400"
        aria-hidden="true"
      />
      <button
        v-if="canOpen && displayText"
        type="button"
        class="min-w-0 flex-1 text-left text-p-sm text-blue-600 underline-offset-2 hover:underline dark:text-blue-400"
        :title="__('View on map')"
        @click.stop="openMap"
      >
        {{ displayText }}
      </button>
      <span
        v-else-if="displayText"
        class="min-w-0 flex-1 text-p-sm text-ink-gray-8"
      >
        {{ displayText }}
      </span>
      <span v-else class="text-p-sm text-ink-gray-4">—</span>
    </div>
    <template v-else>
      <FormControl
        class="form-control"
        type="textarea"
        :value="address"
        :placeholder="placeholder"
        :debounce="500"
        @change.stop="emit('change', $event.target.value)"
      />
      <button
        v-if="canOpen"
        type="button"
        class="inline-flex items-center gap-1 self-start text-p-sm text-blue-600 hover:underline dark:text-blue-400"
        @click.stop="openMap"
      >
        <span class="lucide-map-pin size-3.5" aria-hidden="true" />
        {{ __('View on map') }}
      </button>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { FormControl } from 'frappe-ui'
import {
  canOpenAmapMarker,
  getPoiDisplayAddress,
  openAmapMarker,
} from '@/utils/amapUri'

const props = defineProps({
  address: { type: String, default: '' },
  district: { type: String, default: '' },
  location: { type: String, default: null },
  poiId: { type: String, default: '' },
  name: { type: String, default: '' },
  readOnly: { type: Boolean, default: true },
  editable: { type: Boolean, default: false },
  placeholder: { type: String, default: '' },
})

const emit = defineEmits(['change'])

const displayText = computed(() =>
  getPoiDisplayAddress(props.address, props.district),
)

const canOpen = computed(() =>
  canOpenAmapMarker({ location: props.location, poiId: props.poiId }),
)

function openMap() {
  openAmapMarker({
    address: props.address,
    district: props.district,
    location: props.location,
    poiId: props.poiId,
    name: props.name,
  })
}
</script>
