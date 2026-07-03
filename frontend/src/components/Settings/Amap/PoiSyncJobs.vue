<template>
  <div class="flex h-full flex-col gap-6 text-ink-gray-8">
    <div class="flex justify-between px-2 pt-2">
      <div class="flex flex-col gap-1 w-9/12">
        <h2 class="text-2xl-semibold">{{ __('POI Sync Jobs') }}</h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'Create region and industry specific Amap POI sync jobs. Each agent manages their own jobs and leads.',
            )
          }}
        </p>
      </div>
      <div class="flex items-center gap-2 w-3/12 justify-end">
        <Button
          v-if="isManager()"
          variant="outline"
          :label="__('Global Settings')"
          icon-left="lucide-settings"
          @click="emit('updateStep', 'settings')"
        />
        <Button
          variant="solid"
          :label="__('New Job')"
          icon-left="lucide-plus"
          @click="emit('updateStep', 'new-job')"
        />
      </div>
    </div>

    <div class="grid grid-cols-4 gap-3 px-2">
      <FormControl
        v-model="filters.status"
        type="select"
        :label="__('Status')"
        :options="statusFilterOptions"
      />
      <FormControl
        v-model="filters.city"
        type="text"
        :label="__('City')"
        :placeholder="__('Filter by city')"
      />
      <FormControl
        v-model="filters.keywords"
        type="text"
        :label="__('Keywords')"
        :placeholder="__('Filter by keywords')"
      />
      <FormControl
        v-model="filters.district"
        type="text"
        :label="__('District')"
        :placeholder="__('Filter by district')"
      />
    </div>

    <div v-if="jobs.loading" class="flex mt-28 justify-center w-full">
      <LoadingIndicator class="size-6" />
    </div>

    <EmptyState
      v-else-if="!filteredJobs.length"
      name="POI Sync Jobs"
      :description="
        __(
          'Create a sync job to fetch POI data from Amap by city, district, and industry keywords.',
        )
      "
      icon="map-pin"
    />

    <div v-else class="flex flex-col overflow-hidden">
      <div class="flex items-center py-2 px-4 text-sm text-ink-gray-5">
        <div class="w-3/12">{{ __('Job') }}</div>
        <div class="w-2/12">{{ __('Search') }}</div>
        <div class="w-2/12">{{ __('Region') }}</div>
        <div class="w-1/12">{{ __('Status') }}</div>
        <div class="w-2/12">{{ __('Stats') }}</div>
        <div class="w-2/12">{{ __('Owner') }}</div>
      </div>
      <div class="h-px border-t mx-4 border-outline-elevation-2" />
      <ul class="overflow-y-auto px-2">
        <li
          v-for="job in filteredJobs"
          :key="job.name"
          class="flex items-center justify-between p-3 cursor-pointer hover:bg-surface-sidebar rounded"
          @click="emit('updateStep', 'job-detail', { ...job })"
        >
          <div class="w-3/12 truncate text-p-base-medium">{{ job.name }}</div>
          <div class="w-2/12 truncate">{{ job.keywords }}</div>
          <div class="w-2/12 truncate">
            {{ [job.city, job.district].filter(Boolean).join(' / ') }}
          </div>
          <div class="w-1/12">
            <Badge :theme="STATUS_COLORS[job.status] || 'gray'" size="sm">
              {{ __(job.status) }}
            </Badge>
          </div>
          <div class="w-2/12 text-sm text-ink-gray-6">
            {{ __('{0} POI / {1} leads', [job.total_fetched || 0, job.leads_created || 0]) }}
          </div>
          <div class="w-2/12 truncate text-sm">{{ job.job_owner }}</div>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import EmptyState from '@/components/ListViews/EmptyState.vue'
import { usersStore } from '@/stores/users'
import { Badge } from 'frappe-ui'
import { computed, inject, reactive } from 'vue'
import { STATUS_COLORS } from './amapConfig'

const emit = defineEmits(['updateStep'])
const jobs = inject('poiSyncJobs')
const { isManager } = usersStore()

const filters = reactive({
  status: '',
  city: '',
  keywords: '',
  district: '',
})

const statusFilterOptions = [
  { label: __('All'), value: '' },
  { label: __('Draft'), value: 'Draft' },
  { label: __('Running'), value: 'Running' },
  { label: __('Completed'), value: 'Completed' },
  { label: __('Failed'), value: 'Failed' },
]

const filteredJobs = computed(() => {
  let list = jobs.data || []
  if (filters.status) {
    list = list.filter((job) => job.status === filters.status)
  }
  if (filters.city) {
    list = list.filter((job) =>
      (job.city || '').toLowerCase().includes(filters.city.toLowerCase()),
    )
  }
  if (filters.keywords) {
    list = list.filter((job) =>
      (job.keywords || '').toLowerCase().includes(filters.keywords.toLowerCase()),
    )
  }
  if (filters.district) {
    list = list.filter((job) =>
      (job.district || '').toLowerCase().includes(filters.district.toLowerCase()),
    )
  }
  return list
})
</script>
