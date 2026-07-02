<template>
  <div class="flex-1 p-6">
    <AmapSettings
      v-if="step === 'settings'"
      @updateStep="updateStep"
    />
    <PoiSyncJobForm
      v-else-if="step === 'new-job'"
      :jobData="job"
      @updateStep="updateStep"
    />
    <PoiSyncJobPage
      v-else-if="step === 'job-detail'"
      :jobName="job?.name"
      @updateStep="updateStep"
    />
    <PoiSyncJobs
      v-else
      @updateStep="updateStep"
    />
  </div>
</template>

<script setup>
import { createListResource } from 'frappe-ui'
import { provide, ref } from 'vue'
import AmapSettings from './AmapSettings.vue'
import PoiSyncJobForm from './PoiSyncJobForm.vue'
import PoiSyncJobPage from './PoiSyncJobPage.vue'
import PoiSyncJobs from './PoiSyncJobs.vue'
import { POI_SYNC_JOB_DOCTYPE } from './amapConfig'

const step = ref('job-list')
const job = ref(null)

const jobs = createListResource({
  type: 'list',
  doctype: POI_SYNC_JOB_DOCTYPE,
  cache: 'poi_sync_jobs',
  fields: [
    'name',
    'status',
    'keywords',
    'city',
    'district',
    'job_owner',
    'total_fetched',
    'leads_created',
    'modified',
  ],
  auto: true,
  orderBy: 'modified desc',
  pageLength: 20,
})

provide('poiSyncJobs', jobs)

function updateStep(newStep, data) {
  step.value = newStep
  job.value = data || null
}
</script>
