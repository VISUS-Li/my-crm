<template>
  <div class="flex min-h-0 flex-col gap-6 px-5 pb-6 pt-2 text-ink-gray-8">
    <div class="flex justify-between">
      <Button
        variant="ghost"
        icon-left="lucide-chevron-left"
        :label="isLocal ? __('New Sync Job') : syncJob.name"
        class="text-2xl-semibold -ml-4"
        @click="emit('updateStep', 'job-list')"
      />
      <div class="flex gap-2">
        <Button
          v-if="!isLocal"
          variant="outline"
          :label="__('Preview Search')"
          :loading="previewing"
          @click="previewSearch"
        />
        <Button
          variant="solid"
          :label="isLocal ? __('Create') : __('Update')"
          :loading="saving"
          @click="saveJob"
        />
      </div>
    </div>

    <div class="grid grid-cols-2 gap-4">
      <div class="col-span-2 text-p-base-medium text-ink-gray-7">
        {{ __('Search Criteria') }}
      </div>

      <PresetMultiPicker
        v-model="syncJob.keywords"
        :groups="keywordPickerGroups"
        required
        class="col-span-2"
        :label="__('Industry Keywords')"
        :description="
          __(
            'Pick one or more industry keywords. Select a whole category or specific subcategories.',
          )
        "
        :placeholder="__('Add keywords')"
        allow-custom
        :custom-label="__('Custom Keyword')"
        :custom-placeholder="__('Or type your own keyword, e.g. milk tea shop')"
      />

      <div class="col-span-2 text-p-base-medium text-ink-gray-7">
        {{ __('Region') }}
      </div>
      <ChinaRegionPicker
        v-model:province="syncJob.province"
        v-model:city="syncJob.city"
        v-model:district="syncJob.district"
        v-model:adcode="syncJob.adcode"
      />

      <div class="col-span-2 text-p-base-medium text-ink-gray-7">
        {{ __('Import Settings') }}
      </div>
      <Link
        v-model="syncJob.lead_source"
        doctype="CRM Lead Source"
        :label="__('Lead Source')"
        :placeholder="__('Select lead source')"
      />
      <Link
        v-model="syncJob.assign_to"
        doctype="User"
        :label="__('Assign Leads To')"
        :placeholder="__('Select user')"
      />
      <div class="col-span-2 flex items-center gap-2 pb-2">
        <Switch v-model="syncJob.import_only_with_phone" size="sm" />
        <span class="text-p-sm">{{ __('Import only POIs with phone') }}</span>
      </div>
    </div>

    <div v-if="previewResults.length" class="rounded-lg border p-4 space-y-3">
      <div class="text-base-medium">
        {{ __('Preview Results') }} ({{ previewResults.length }})
      </div>
      <div
        v-for="poi in previewResults"
        :key="poi.id"
        class="grid grid-cols-4 gap-2 text-p-sm border-b pb-2"
      >
        <div class="truncate">{{ poi.name }}</div>
        <div>{{ poi.tel || __('No phone') }}</div>
        <div class="truncate">{{ poi.address }}</div>
        <div class="truncate">{{ poi.adname || poi.cityname }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Switch, toast, call } from 'frappe-ui'
import { computed, inject, ref } from 'vue'
import Link from '@/components/Controls/Link.vue'
import ChinaRegionPicker from './ChinaRegionPicker.vue'
import PresetMultiPicker from './PresetMultiPicker.vue'
import { POI_SYNC_JOB_DOCTYPE } from './amapConfig'
import { buildKeywordPickerGroups } from '@/config/poiSyncOptions'

const props = defineProps({
  jobData: {
    type: Object,
    default: null,
  },
})

const emit = defineEmits(['updateStep'])
const jobs = inject('poiSyncJobs')

const previewResults = ref([])
const previewing = ref(false)
const saving = ref(false)

const isLocal = computed(() => !props.jobData?.name)
const keywordPickerGroups = buildKeywordPickerGroups()

const defaultJob = () => ({
  doctype: POI_SYNC_JOB_DOCTYPE,
  naming_series: 'POI-.YYYY.-.#####',
  status: 'Draft',
  keywords: '',
  types: '',
  province: '',
  city: '',
  district: '',
  adcode: '',
  bbox: '',
  lead_source: '高德地图',
  assign_to: '',
  import_only_with_phone: 1,
})

const syncJob = ref(props.jobData?.name ? { ...defaultJob(), ...props.jobData } : defaultJob())

async function saveJob() {
  if (!syncJob.value.keywords?.trim() || !syncJob.value.city) {
    toast.error(__('Please select at least one keyword and a city'))
    return
  }

  saving.value = true
  try {
    if (isLocal.value) {
      await jobs.insert.submit(syncJob.value)
      toast.success(__('Sync job created'))
    } else {
      await jobs.setValue.submit({
        name: syncJob.value.name,
        ...syncJob.value,
      })
      toast.success(__('Sync job updated'))
    }
    jobs.reload()
    emit('updateStep', 'job-list')
  } catch (error) {
    toast.error(error.messages?.[0] || __('Failed to save sync job'))
  } finally {
    saving.value = false
  }
}

async function previewSearch() {
  previewing.value = true
  try {
    const result = await call('crm.amap.api.preview_search', {
      keywords: syncJob.value.keywords,
      city: syncJob.value.city,
      types: syncJob.value.types || '',
      limit: 10,
    })
    previewResults.value = result?.pois || []
  } catch (error) {
    toast.error(error.messages?.[0] || __('Preview failed'))
  } finally {
    previewing.value = false
  }
}
</script>
