<template>
  <div class="flex h-full flex-col gap-6 text-ink-gray-8 px-2 pt-2">
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
      <FormControl
        v-model="syncJob.keywords"
        type="text"
        required
        :label="__('Keywords')"
        :placeholder="__('e.g. 奶茶, 美容, 餐饮')"
      />
      <FormControl
        v-model="syncJob.types"
        type="text"
        :label="__('POI Types')"
        :placeholder="__('Optional type codes, separated by |')"
      />
      <FormControl
        v-model="syncJob.province"
        type="text"
        :label="__('Province')"
      />
      <FormControl
        v-model="syncJob.city"
        type="text"
        required
        :label="__('City')"
      />
      <FormControl
        v-model="syncJob.district"
        type="text"
        :label="__('District')"
      />
      <FormControl
        v-model="syncJob.adcode"
        type="text"
        :label="__('Adcode')"
        :placeholder="__('Optional district code for precise area')"
      />
      <FormControl
        v-model="syncJob.bbox"
        type="text"
        :label="__('Bounding Box')"
        :placeholder="__('min_lng,min_lat,max_lng,max_lat')"
      />
      <FormControl
        v-model="syncJob.lead_source"
        type="link"
        doctype="CRM Lead Source"
        :label="__('Lead Source')"
      />
      <FormControl
        v-model="syncJob.assign_to"
        type="link"
        doctype="User"
        :label="__('Assign Leads To')"
      />
      <div class="flex items-center gap-2 self-end pb-2">
        <Switch v-model="syncJob.import_only_with_phone" size="sm" />
        <span class="text-sm">{{ __('Import only POIs with phone') }}</span>
      </div>
    </div>

    <div v-if="previewResults.length" class="rounded-lg border p-4 space-y-3">
      <div class="text-p-base-medium">
        {{ __('Preview Results') }} ({{ previewResults.length }})
      </div>
      <div
        v-for="poi in previewResults"
        :key="poi.id"
        class="grid grid-cols-4 gap-2 text-sm border-b pb-2"
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
import { POI_SYNC_JOB_DOCTYPE } from './amapConfig'

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
  if (!syncJob.value.keywords || !syncJob.value.city) {
    toast.error(__('Keywords and city are required'))
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
