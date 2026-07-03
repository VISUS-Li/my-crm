<template>
  <FormControl
    v-if="filter.fieldtype == 'Check'"
    v-model="filter.value"
    :label="displayLabel"
    type="checkbox"
    @change.stop="updateFilter(filter, $event.target.checked)"
  />
  <FormControl
    v-else-if="filter.fieldtype === 'Select'"
    v-model="filter.value"
    class="form-control cursor-pointer [&_select]:cursor-pointer"
    type="select"
    :options="displayOptions"
    :placeholder="displayLabel"
    @update:modelValue="updateFilter(filter, $event)"
  />
  <Link
    v-else-if="filter.fieldtype === 'Link'"
    :value="filter.value"
    :doctype="filter.options"
    :placeholder="displayLabel"
    @change="(data) => updateFilter(filter, data)"
  />
  <component
    :is="filter.fieldtype === 'Date' ? DatePicker : DateTimePicker"
    v-else-if="['Date', 'Datetime'].includes(filter.fieldtype)"
    class="border-none"
    :value="filter.value"
    :placeholder="displayLabel"
    @change="(v) => updateFilter(filter, v)"
  />
  <FormControl
    v-else
    v-model="filter.value"
    type="text"
    :placeholder="displayLabel"
    @input.stop="debouncedFn(filter, $event.target.value)"
  />
</template>
<script setup>
import Link from '@/components/Controls/Link.vue'
import { FormControl, DatePicker, DateTimePicker } from 'frappe-ui'
import { useDebounceFn } from '@vueuse/core'
import { reactive, watch, computed } from 'vue'
import { translateLabel, translateSelectOptions } from '@/utils/translateField'

const props = defineProps({
  filter: { type: Object, required: true },
})

const filter = reactive(props.filter)

const displayLabel = computed(() => translateLabel(filter.label))
const displayOptions = computed(() => translateSelectOptions(filter.options))

const emit = defineEmits(['applyQuickFilter'])

watch(
  () => props.filter,
  (newFilter) => Object.assign(filter, newFilter),
  { deep: true },
)

const debouncedFn = useDebounceFn((f, value) => {
  emit('applyQuickFilter', f, value)
}, 500)

function updateFilter(f, value) {
  emit('applyQuickFilter', f, value)
}
</script>
