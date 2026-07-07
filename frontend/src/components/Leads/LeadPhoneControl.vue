<template>
  <div class="flex w-full flex-col gap-2">
    <div v-if="showCallAction" class="flex flex-wrap items-center gap-2">
      <a
        :href="telHref"
        class="inline-flex min-h-11 w-full items-center justify-center gap-2.5 rounded-xl bg-ink-green-2 px-4 py-3 text-base font-semibold text-white shadow-md transition hover:bg-ink-green-3 active:scale-[0.98] sm:w-auto sm:min-w-[200px]"
        @click.stop
      >
        <PhoneIcon class="size-5 shrink-0" />
        <span class="truncate">{{ displayValue }}</span>
      </a>
      <Button
        v-if="!readOnly"
        variant="ghost"
        size="sm"
        class="!h-8"
        :label="__('Edit')"
        @click.stop="startEditing"
      />
    </div>

    <div
      v-else-if="displayValue && !editing"
      class="flex min-h-7 flex-wrap items-center gap-2"
    >
      <span class="truncate text-p-base font-medium text-ink-gray-9">{{
        displayValue
      }}</span>
      <Popover v-if="leadId && showQrAction" placement="bottom-end">
        <template #target="{ togglePopover }">
          <Button
            variant="outline"
            size="sm"
            class="!h-8 shrink-0 border-ink-blue-2 text-ink-blue-3"
            :label="__('Scan on phone')"
            icon="smartphone"
            @click.stop="openQrPopover(togglePopover)"
          />
        </template>
        <template #body>
          <div class="flex w-56 flex-col items-center gap-3 p-4">
            <div class="text-center text-p-sm text-ink-gray-7">
              {{ __('Scan to open this lead on your phone and call directly') }}
            </div>
            <img
              v-if="qrDataUrl"
              :src="qrDataUrl"
              :alt="__('Scan on phone')"
              class="size-40 rounded border border-outline-gray-2 bg-white p-2"
              width="160"
              height="160"
            />
            <div
              v-else-if="qrError"
              class="flex size-40 items-center justify-center rounded border border-outline-gray-2 bg-surface-gray-1 p-3 text-center text-p-xs text-ink-red-4"
            >
              {{ qrError }}
            </div>
            <div
              v-else
              class="size-40 animate-pulse rounded border border-outline-gray-2 bg-surface-gray-1"
            />
          </div>
        </template>
      </Popover>
      <Button
        v-if="!readOnly"
        variant="ghost"
        size="sm"
        class="!h-7 !px-2"
        :tooltip="__('Edit')"
        icon="edit"
        @click.stop="startEditing"
      />
    </div>

    <FormControl
      v-if="editing || (!displayValue && !readOnly)"
      class="form-control"
      type="text"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="readOnly"
      :debounce="500"
      @change.stop="onInput"
    />
  </div>
</template>

<script setup>
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import {
  getLeadPageUrl,
  isTouchPhoneDevice,
  normalizePhoneForTel,
} from '@/utils/leadContact'
import { isMobileView } from '@/composables/settings'
import { Button, FormControl, Popover } from 'frappe-ui'
import QRCode from 'qrcode'
import { computed, ref, watch } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  leadId: { type: String, default: '' },
  readOnly: { type: Boolean, default: false },
  placeholder: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue', 'change'])

const editing = ref(false)
const qrDataUrl = ref('')
const qrError = ref('')

const displayValue = computed(() => props.modelValue || '')
const telHref = computed(() => {
  const normalized = normalizePhoneForTel(props.modelValue)
  return normalized ? `tel:${normalized}` : ''
})
const isPhoneClient = computed(
  () => isMobileView.value || isTouchPhoneDevice(),
)
const showCallAction = computed(
  () => Boolean(telHref.value) && !editing.value && isPhoneClient.value,
)
const showQrAction = computed(
  () => Boolean(props.leadId) && !isPhoneClient.value,
)
const leadPageUrl = computed(() => getLeadPageUrl(props.leadId))

async function renderQr() {
  qrError.value = ''
  if (!leadPageUrl.value) {
    qrDataUrl.value = ''
    qrError.value = __('Unable to build page link')
    return
  }

  try {
    qrDataUrl.value = await QRCode.toDataURL(leadPageUrl.value, {
      width: 160,
      margin: 1,
      errorCorrectionLevel: 'M',
    })
  } catch {
    qrDataUrl.value = ''
    qrError.value = __('Failed to generate QR code')
  }
}

function openQrPopover(togglePopover) {
  if (!qrDataUrl.value && !qrError.value) {
    renderQr()
  }
  togglePopover()
}

function startEditing() {
  editing.value = true
}

function onInput(event) {
  const value = event.target.value
  emit('update:modelValue', value)
  emit('change', value)
  if (value) editing.value = false
}

watch(
  [leadPageUrl, showQrAction],
  () => {
    qrDataUrl.value = ''
    qrError.value = ''
    if (showQrAction.value) renderQr()
  },
  { immediate: true },
)
</script>
