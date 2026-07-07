<template>
  <div class="col-span-2 space-y-2">
    <div v-if="label" class="text-p-sm-medium text-ink-gray-7">
      {{ label }}
      <span v-if="required" class="text-red-500">*</span>
    </div>
    <div v-if="description" class="text-p-sm text-ink-gray-5">
      {{ description }}
    </div>

    <div
      class="min-h-9 rounded border border-outline-gray-2 bg-surface-base px-2 py-1.5"
    >
      <div v-if="selectedValues.length" class="mb-1.5 flex flex-wrap gap-1.5">
        <button
          v-for="value in selectedValues"
          :key="value"
          type="button"
          class="inline-flex max-w-full items-center gap-1 rounded-full border border-outline-gray-2 bg-surface-gray-1 px-2.5 py-0.5 text-p-sm text-ink-gray-7 hover:bg-surface-gray-2"
          @click="removeValue(value)"
        >
          <span class="truncate">{{ displayLabel(value) }}</span>
          <span class="lucide-x size-3.5 shrink-0 text-ink-gray-5" aria-hidden="true" />
        </button>
      </div>

      <Popover v-model:show="open" placement="bottom-start">
        <template #target="{ togglePopover }">
          <button
            type="button"
            class="flex w-full items-center gap-2 rounded px-1 py-0.5 text-left text-p-sm text-ink-gray-5 hover:text-ink-gray-7"
            @click="togglePopover()"
          >
            <span class="lucide-plus size-4 shrink-0" aria-hidden="true" />
            <span>{{ placeholder || __('Add selection') }}</span>
          </button>
        </template>
        <template #body="{ isOpen }">
          <div
            v-show="isOpen"
            class="mt-1 w-[min(32rem,calc(100vw-2rem))] rounded-lg bg-surface-elevation-2 p-2 shadow-2xl ring-1 ring-black/5"
          >
            <TextInput
              v-model="query"
              :placeholder="__('Search')"
              :debounce="150"
              class="mb-2"
            >
              <template #prefix>
                <span class="lucide-search size-4 text-ink-gray-5" aria-hidden="true" />
              </template>
            </TextInput>

            <div
              v-if="filteredGroups.length === 0"
              class="px-2 py-6 text-center text-p-sm text-ink-gray-5"
            >
              {{ __('No results found') }}
            </div>

            <div
              v-else-if="query.trim()"
              class="max-h-64 space-y-3 overflow-y-auto px-1"
            >
              <div
                v-for="group in filteredGroups"
                :key="group.group"
                class="space-y-1"
              >
                <div class="px-1 text-p-sm-medium text-ink-gray-5">
                  {{ __(group.group) }}
                </div>
                <label
                  v-if="group.categoryValue"
                  class="flex cursor-pointer items-center gap-2 rounded px-2 py-1.5 hover:bg-surface-gray-2"
                >
                  <input
                    type="checkbox"
                    class="rounded border-outline-gray-3"
                    :checked="isSelected(group.categoryValue)"
                    @change="toggleValue(group.categoryValue)"
                  />
                  <span class="text-p-sm text-ink-gray-7">
                    {{ __('All {0}', [__(group.group)]) }}
                    <span class="text-ink-gray-5">({{ group.categoryValue }})</span>
                  </span>
                </label>
                <label
                  v-for="item in group.items"
                  :key="item.value"
                  class="flex cursor-pointer items-center gap-2 rounded px-2 py-1.5 hover:bg-surface-gray-2"
                >
                  <input
                    type="checkbox"
                    class="rounded border-outline-gray-3"
                    :checked="isSelected(item.value)"
                    @change="toggleValue(item.value)"
                  />
                  <span class="truncate text-p-sm text-ink-gray-7">
                    {{ formatItemLabel(item) }}
                  </span>
                </label>
              </div>
            </div>

            <div v-else class="grid max-h-72 grid-cols-[9rem,1fr] overflow-hidden rounded border border-outline-gray-2">
              <div class="overflow-y-auto border-r border-outline-gray-2 bg-surface-gray-1">
                <button
                  v-for="group in normalizedGroups"
                  :key="group.group"
                  type="button"
                  class="block w-full truncate px-3 py-2 text-left text-p-sm transition-colors"
                  :class="
                    activeGroup === group.group
                      ? 'bg-surface-base font-medium text-ink-gray-8'
                      : 'text-ink-gray-6 hover:bg-surface-gray-2'
                  "
                  @click="activeGroup = group.group"
                >
                  {{ __(group.group) }}
                </button>
              </div>
              <div class="overflow-y-auto p-2">
                <template v-if="activeGroupData">
                  <label
                    v-if="activeGroupData.categoryValue"
                    class="mb-1 flex cursor-pointer items-center gap-2 rounded px-2 py-1.5 hover:bg-surface-gray-2"
                  >
                    <input
                      type="checkbox"
                      class="rounded border-outline-gray-3"
                      :checked="isSelected(activeGroupData.categoryValue)"
                      @change="toggleValue(activeGroupData.categoryValue)"
                    />
                    <span class="text-p-sm text-ink-gray-7">
                      {{ __('All {0}', [__(activeGroupData.group)]) }}
                      <span class="text-ink-gray-5">
                        ({{ activeGroupData.categoryValue }})
                      </span>
                    </span>
                  </label>
                  <div
                    v-if="activeGroupData.items.length"
                    class="mb-2 flex items-center justify-between px-2"
                  >
                    <span class="text-p-sm text-ink-gray-5">
                      {{ __('Subcategories') }}
                    </span>
                    <button
                      type="button"
                      class="text-p-sm text-ink-blue-6 hover:underline"
                      @click="toggleGroupItems(activeGroupData)"
                    >
                      {{
                        isGroupFullySelected(activeGroupData)
                          ? __('Clear subcategories')
                          : __('Select all subcategories')
                      }}
                    </button>
                  </div>
                  <label
                    v-for="item in activeGroupData.items"
                    :key="item.value"
                    class="flex cursor-pointer items-center gap-2 rounded px-2 py-1.5 hover:bg-surface-gray-2"
                  >
                    <input
                      type="checkbox"
                      class="rounded border-outline-gray-3"
                      :checked="isSelected(item.value)"
                      @change="toggleValue(item.value)"
                    />
                    <span class="truncate text-p-sm text-ink-gray-7">
                      {{ formatItemLabel(item) }}
                    </span>
                  </label>
                </template>
              </div>
            </div>
          </div>
        </template>
      </Popover>
    </div>

    <div v-if="allowCustom" class="flex gap-2">
      <FormControl
        v-model="customValue"
        type="text"
        class="flex-1"
        :label="customLabel || __('Custom value')"
        :placeholder="customPlaceholder"
        @keydown.enter.prevent="addCustomValue"
      />
      <Button
        class="mt-5"
        variant="subtle"
        :label="__('Add')"
        :disabled="!customValue?.trim()"
        @click="addCustomValue"
      />
    </div>
  </div>
</template>

<script setup>
import { Button, Popover, TextInput } from 'frappe-ui'
import { computed, ref, watch } from 'vue'
import {
  filterOptionGroups,
  findOptionLabel,
  joinDelimitedValues,
  normalizeOptionGroups,
  isPresetValue,
  parseDelimitedValues,
} from '@/utils/poiSyncSelection'

const props = defineProps({
  modelValue: { type: String, default: '' },
  groups: { type: Array, default: () => [] },
  label: { type: String, default: '' },
  description: { type: String, default: '' },
  placeholder: { type: String, default: '' },
  required: { type: Boolean, default: false },
  showCodeInLabel: { type: Boolean, default: false },
  allowCustom: { type: Boolean, default: false },
  customLabel: { type: String, default: '' },
  customPlaceholder: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue'])

const open = ref(false)
const query = ref('')
const customValue = ref('')
const activeGroup = ref('')

const normalizedGroups = computed(() => normalizeOptionGroups(props.groups))
const filteredGroups = computed(() => filterOptionGroups(props.groups, query.value))

const selectedValues = computed(() => parseDelimitedValues(props.modelValue))

const activeGroupData = computed(
  () =>
    normalizedGroups.value.find((group) => group.group === activeGroup.value) ||
    normalizedGroups.value[0] ||
    null,
)

watch(
  normalizedGroups,
  (groups) => {
    if (!activeGroup.value && groups.length) {
      activeGroup.value = groups[0].group
    }
  },
  { immediate: true },
)

function displayLabel(value) {
  if (isPresetValue(props.groups, value)) {
    const label = findOptionLabel(props.groups, value)
    if (props.showCodeInLabel) {
      return `${__(label)} (${value})`
    }
    return __(label)
  }
  return value
}

function formatItemLabel(item) {
  if (props.showCodeInLabel && item.value) {
    return `${__(item.label)} (${item.value})`
  }
  return __(item.label)
}

function isSelected(value) {
  return selectedValues.value.includes(value)
}

function emitValues(values) {
  emit('update:modelValue', joinDelimitedValues(values))
}

function toggleValue(value) {
  const next = new Set(selectedValues.value)
  if (next.has(value)) {
    next.delete(value)
  } else {
    next.add(value)
  }
  emitValues([...next])
}

function removeValue(value) {
  emitValues(selectedValues.value.filter((item) => item !== value))
}

function isGroupFullySelected(group) {
  const itemValues = group.items.map((item) => item.value)
  return itemValues.length > 0 && itemValues.every((value) => isSelected(value))
}

function toggleGroupItems(group) {
  const next = new Set(selectedValues.value)
  const itemValues = group.items.map((item) => item.value)
  const allSelected = itemValues.every((value) => next.has(value))

  if (allSelected) {
    itemValues.forEach((value) => next.delete(value))
  } else {
    itemValues.forEach((value) => next.add(value))
  }
  emitValues([...next])
}

function addCustomValue() {
  const value = customValue.value?.trim()
  if (!value || isSelected(value)) {
    customValue.value = ''
    return
  }
  emitValues([...selectedValues.value, value])
  customValue.value = ''
}
</script>
