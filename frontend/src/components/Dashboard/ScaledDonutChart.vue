<template>
  <ECharts :options="options" :error="error" />
</template>

<script setup>
import { computed, ref } from 'vue'
import { ECharts } from 'frappe-ui'
import useDonutChartOptions from 'frappe-ui/charts/donutChartOptions'
import { useFontScale } from '@/composables/useFontScale'
import { scaleChartOptions } from '@/utils/chartFontScale'

const props = defineProps({
  config: { type: Object, required: true },
})

const { currentFontScale } = useFontScale()
const error = ref('')

const options = computed(() => {
  try {
    const config = {
      ...props.config,
      dir:
        props.config.dir ??
        (typeof document !== 'undefined' &&
        document.documentElement.dir === 'rtl'
          ? 'rtl'
          : 'ltr'),
    }
    return scaleChartOptions(
      useDonutChartOptions(config),
      currentFontScale.value,
    )
  } catch (e) {
    error.value = e.message
    return {}
  }
})
</script>
