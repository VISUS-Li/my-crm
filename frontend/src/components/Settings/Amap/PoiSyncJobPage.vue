<template>
  <div class="flex h-full flex-col gap-6 text-ink-gray-8 px-2 pt-2">
    <div class="flex justify-between">
      <Button
        variant="ghost"
        icon-left="lucide-chevron-left"
        :label="job?.name || __('Job Detail')"
        class="text-2xl-semibold -ml-4"
        @click="emit('updateStep', 'job-list')"
      />
      <div class="flex gap-2">
        <Button
          v-if="canCancel"
          variant="outline"
          theme="red"
          :label="__('Cancel')"
          :loading="cancelling"
          @click="cancelJob"
        />
        <Button
          v-if="canStart"
          variant="solid"
          :label="__('Start Sync')"
          icon-left="lucide-play"
          :loading="starting"
          @click="startJob"
        />
        <Button
          variant="outline"
          :label="__('Edit')"
          @click="emit('updateStep', 'new-job', job)"
        />
      </div>
    </div>

    <div v-if="loading" class="flex justify-center mt-20">
      <LoadingIndicator class="size-6" />
    </div>

    <template v-else-if="job">
      <div class="grid grid-cols-4 gap-4">
        <div class="rounded-lg border p-4">
          <div class="text-sm text-ink-gray-5">{{ __('Status') }}</div>
          <Badge :theme="STATUS_COLORS[job.status] || 'gray'" class="mt-2">
            {{ job.status }}
          </Badge>
        </div>
        <div class="rounded-lg border p-4">
          <div class="text-sm text-ink-gray-5">{{ __('Total POI') }}</div>
          <div class="text-2xl-semibold mt-2">{{ job.total_fetched || 0 }}</div>
        </div>
        <div class="rounded-lg border p-4">
          <div class="text-sm text-ink-gray-5">{{ __('With Phone') }}</div>
          <div class="text-2xl-semibold mt-2">{{ job.with_phone_count || 0 }}</div>
        </div>
        <div class="rounded-lg border p-4">
          <div class="text-sm text-ink-gray-5">{{ __('Leads Created') }}</div>
          <div class="text-2xl-semibold mt-2">{{ job.leads_created || 0 }}</div>
        </div>
      </div>

      <div class="grid grid-cols-2 gap-4">
        <div class="rounded-lg border p-4 space-y-2">
          <div><span class="text-ink-gray-5">{{ __('Keywords') }}:</span> {{ job.keywords }}</div>
          <div><span class="text-ink-gray-5">{{ __('City') }}:</span> {{ job.city }}</div>
          <div><span class="text-ink-gray-5">{{ __('District') }}:</span> {{ job.district || '-' }}</div>
          <div><span class="text-ink-gray-5">{{ __('Owner') }}:</span> {{ job.job_owner }}</div>
        </div>
        <div class="rounded-lg border p-4 space-y-2">
          <div><span class="text-ink-gray-5">{{ __('Started') }}:</span> {{ formatDate(job.started_at) }}</div>
          <div><span class="text-ink-gray-5">{{ __('Completed') }}:</span> {{ formatDate(job.completed_at) }}</div>
          <div><span class="text-ink-gray-5">{{ __('Skipped') }}:</span> {{ job.leads_skipped || 0 }}</div>
          <div><span class="text-ink-gray-5">{{ __('Progress') }}:</span> {{ job.progress_message || '-' }}</div>
        </div>
      </div>

      <div v-if="job.error_log" class="rounded-lg border border-red-200 bg-red-50 p-4">
        <div class="text-p-base-medium text-red-700">{{ __('Error Log') }}</div>
        <pre class="mt-2 whitespace-pre-wrap text-sm text-red-700">{{ job.error_log }}</pre>
      </div>
    </template>
  </div>
</template>

<script setup>
import { Badge, toast, call } from 'frappe-ui'
import { computed, inject, onBeforeUnmount, onMounted, ref } from 'vue'
import { STATUS_COLORS } from './amapConfig'

const props = defineProps({
  jobName: {
    type: String,
    required: true,
  },
})

const emit = defineEmits(['updateStep'])
const jobs = inject('poiSyncJobs')

const job = ref(null)
const loading = ref(true)
const starting = ref(false)
const cancelling = ref(false)
let pollTimer = null

const canStart = computed(() =>
  ['Draft', 'Completed', 'Failed', 'Cancelled'].includes(job.value?.status),
)
const canCancel = computed(() => ['Running', 'Queued'].includes(job.value?.status))

function formatDate(value) {
  return value || '-'
}

async function fetchProgress() {
  if (!props.jobName) return
  try {
    const result = await call('crm.amap.api.get_job_progress', {
      job_name: props.jobName,
    })
    job.value = result
    if (['Running', 'Queued'].includes(result.status)) {
      schedulePoll()
    } else {
      clearPoll()
      jobs.reload()
    }
  } catch (error) {
    toast.error(error.messages?.[0] || __('Failed to load job progress'))
  } finally {
    loading.value = false
  }
}

function schedulePoll() {
  clearPoll()
  pollTimer = setTimeout(fetchProgress, 3000)
}

function clearPoll() {
  if (pollTimer) {
    clearTimeout(pollTimer)
    pollTimer = null
  }
}

async function startJob() {
  starting.value = true
  try {
    await call('crm.amap.api.start_sync_job', { job_name: props.jobName })
    toast.success(__('Sync started'))
    await fetchProgress()
  } catch (error) {
    toast.error(error.messages?.[0] || __('Failed to start sync'))
  } finally {
    starting.value = false
  }
}

async function cancelJob() {
  cancelling.value = true
  try {
    await call('crm.amap.api.cancel_sync_job', { job_name: props.jobName })
    toast.success(__('Sync cancelled'))
    await fetchProgress()
  } catch (error) {
    toast.error(error.messages?.[0] || __('Failed to cancel sync'))
  } finally {
    cancelling.value = false
  }
}

onMounted(fetchProgress)
onBeforeUnmount(clearPoll)
</script>
