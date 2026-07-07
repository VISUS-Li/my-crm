<template>
  <div class="flex h-full min-h-0 flex-col gap-6 overflow-y-auto text-ink-gray-8 px-2 pt-2">
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
          v-if="showActivateLicense"
          variant="outline"
          :label="__('Activate License')"
          icon-left="lucide-key-round"
          @click="openLicenseDialog"
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
      <div
        v-if="['Queued', 'Running'].includes(job.status)"
        class="rounded-lg border border-blue-200 bg-blue-50 p-4 text-p-sm text-blue-800"
      >
        <div class="flex items-center gap-2">
          <LoadingIndicator class="size-4" />
          <span>{{ __(job.progress_message || 'Processing...') }}</span>
        </div>
        <p v-if="job.status === 'Queued'" class="mt-2 text-blue-700">
          {{
            __(
              'If this stays queued for more than a minute, ensure the Frappe background worker is running (bench start or worker-long).',
            )
          }}
        </p>
      </div>

      <div class="grid grid-cols-4 gap-4">
        <div class="rounded-lg border p-4">
          <div class="text-p-sm text-ink-gray-5">{{ __('Status') }}</div>
          <Badge :theme="STATUS_COLORS[job.status] || 'gray'" class="mt-2">
            {{ __(job.status) }}
          </Badge>
        </div>
        <div class="rounded-lg border p-4">
          <div class="text-p-sm text-ink-gray-5">{{ __('Total POI') }}</div>
          <div class="text-2xl-semibold mt-2">{{ job.total_fetched || 0 }}</div>
        </div>
        <div class="rounded-lg border p-4">
          <div class="text-p-sm text-ink-gray-5">{{ __('With Phone') }}</div>
          <div class="text-2xl-semibold mt-2">{{ job.with_phone_count || 0 }}</div>
        </div>
        <div class="rounded-lg border p-4">
          <div class="text-p-sm text-ink-gray-5">{{ __('Leads Created') }}</div>
          <div class="text-2xl-semibold mt-2">{{ job.leads_created || 0 }}</div>
        </div>
      </div>

      <div class="grid grid-cols-2 gap-4">
        <div class="rounded-lg border p-4 space-y-2">
          <div><span class="text-ink-gray-5">{{ __('Keywords') }}:</span> {{ job.keywords }}</div>
          <div><span class="text-ink-gray-5">{{ __('City') }}:</span> {{ job.city }}</div>
          <div><span class="text-ink-gray-5">{{ __('District') }}:</span> {{ job.district || '-' }}</div>
          <div><span class="text-ink-gray-5">{{ __('Owner') }}:</span> {{ ownerLabel(job.job_owner) }}</div>
        </div>
        <div class="rounded-lg border p-4 space-y-2">
          <div><span class="text-ink-gray-5">{{ __('Started') }}:</span> {{ formatDate(job.started_at) }}</div>
          <div><span class="text-ink-gray-5">{{ __('Completed') }}:</span> {{ formatDate(job.completed_at) }}</div>
          <div><span class="text-ink-gray-5">{{ __('Skipped') }}:</span> {{ job.leads_skipped || 0 }}</div>
          <div><span class="text-ink-gray-5">{{ __('Progress') }}:</span> {{ job.progress_message ? __(job.progress_message) : '-' }}</div>
        </div>
      </div>

      <div v-if="job.error_log" class="rounded-lg border border-red-200 bg-red-50 p-4">
        <div class="text-base-medium text-red-700">{{ __('Error Log') }}</div>
        <pre class="mt-2 whitespace-pre-wrap text-p-sm text-red-700">{{ __(job.error_log) }}</pre>
      </div>

      <div v-if="job.segments?.length" class="rounded-lg border overflow-hidden">
        <div class="flex items-center justify-between border-b px-4 py-3">
          <div class="text-base-medium">{{ __('Sync Segments') }}</div>
          <div class="text-p-sm text-ink-gray-5">{{ __('{0} segments', [job.segments.length]) }}</div>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full text-p-sm">
            <thead class="bg-surface-gray-1 text-ink-gray-5">
              <tr>
                <th class="px-4 py-2 text-left">{{ __('Keyword') }}</th>
                <th class="px-4 py-2 text-left">{{ __('Status') }}</th>
                <th class="px-4 py-2 text-left">{{ __('Fetched') }}</th>
                <th class="px-4 py-2 text-left">{{ __('Reported') }}</th>
                <th class="px-4 py-2 text-left">{{ __('Pages') }}</th>
                <th class="px-4 py-2 text-left">{{ __('Warning') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="segment in job.segments" :key="segment.name" class="border-t">
                <td class="px-4 py-2">{{ segment.keyword || '-' }}</td>
                <td class="px-4 py-2">
                  <Badge :theme="segment.truncated ? 'orange' : STATUS_COLORS[segment.status] || 'gray'" size="sm">
                    {{ __(segment.status) }}
                  </Badge>
                </td>
                <td class="px-4 py-2">{{ segment.fetched_count || 0 }}</td>
                <td class="px-4 py-2">{{ segment.reported_count || 0 }}</td>
                <td class="px-4 py-2">{{ segment.page_count || 0 }}</td>
                <td class="px-4 py-2 max-w-[260px] truncate">
                  <span v-if="segment.truncated" class="text-orange-700">{{ __('Truncated') }}</span>
                  <span v-else-if="segment.error_message" class="text-red-700">{{ segment.error_message }}</span>
                  <span v-else class="text-ink-gray-4">-</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div v-if="job.events?.length" class="rounded-lg border overflow-hidden">
        <div class="border-b px-4 py-3 text-base-medium">{{ __('Recent Sync Events') }}</div>
        <div class="divide-y">
          <div v-for="event in job.events" :key="event.name" class="grid grid-cols-[160px_1fr] gap-3 px-4 py-2 text-p-sm">
            <div class="text-ink-gray-5">{{ __(event.event_type) }}</div>
            <div class="min-w-0">
              <div class="truncate">{{ event.message ? __(event.message) : '-' }}</div>
              <div class="text-p-xs text-ink-gray-4">{{ event.creation }}</div>
            </div>
          </div>
        </div>
      </div>

      <div
        v-if="['Completed', 'Running'].includes(job.status)"
        class="rounded-lg border overflow-hidden"
      >
        <div class="flex items-center justify-between border-b px-4 py-3">
          <div class="text-base-medium">{{ __('Synced Merchants') }}</div>
          <div class="text-p-sm text-ink-gray-5">
            {{ __('{0} records', [poiTotal]) }}
          </div>
        </div>

        <div v-if="poiLoading" class="flex justify-center py-10">
          <LoadingIndicator class="size-5" />
        </div>
        <div v-else-if="!poiRecords.length" class="px-4 py-8 text-center text-p-sm text-ink-gray-5">
          {{ __('No POI records yet. Results appear here as sync progresses.') }}
        </div>
        <div v-else class="overflow-x-auto">
          <table class="w-full text-p-sm">
            <thead class="bg-surface-gray-1 text-ink-gray-5">
              <tr>
                <th class="px-4 py-2 text-left">{{ __('Photo') }}</th>
                <th class="px-4 py-2 text-left">{{ __('Name') }}</th>
                <th class="px-4 py-2 text-left">{{ __('Phones') }}</th>
                <th class="px-4 py-2 text-left">{{ __('Address') }}</th>
                <th class="px-4 py-2 text-left">{{ __('District') }}</th>
                <th class="px-4 py-2 text-left">{{ __('Type') }}</th>
                <th class="px-4 py-2 text-left">{{ __('Rating / Cost') }}</th>
                <th class="px-4 py-2 text-left">{{ __('Sync') }}</th>
                <th class="px-4 py-2 text-left">{{ __('Lead') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="record in poiRecords"
                :key="record.name"
                class="border-t hover:bg-surface-gray-1"
              >
                <td class="px-4 py-2">
                  <img
                    v-if="record.primary_photo_url"
                    :src="record.primary_photo_url"
                    :alt="record.name1"
                    class="size-12 rounded object-cover"
                    loading="lazy"
                  />
                  <div v-else class="flex size-12 items-center justify-center rounded bg-surface-gray-2 text-ink-gray-4">
                    -
                  </div>
                </td>
                <td class="px-4 py-2 max-w-[160px] truncate">{{ record.name1 }}</td>
                <td class="px-4 py-2 min-w-[180px]">
                  <div v-if="phoneValues(record).length" class="flex max-w-[220px] flex-wrap gap-1">
                    <Badge
                      v-for="phone in phoneValues(record)"
                      :key="phone"
                      theme="gray"
                      size="sm"
                    >
                      {{ phone }}
                    </Badge>
                  </div>
                  <span v-else class="text-ink-gray-4">{{ __('No phone') }}</span>
                </td>
                <td class="px-4 py-2 max-w-[220px] truncate">{{ record.address || '-' }}</td>
                <td class="px-4 py-2">{{ record.district || record.city || '-' }}</td>
                <td class="px-4 py-2 max-w-[120px] truncate">{{ record.poi_type || '-' }}</td>
                <td class="px-4 py-2">
                  <span v-if="record.rating || record.cost">
                    {{ [record.rating, record.cost ? __('CNY {0}', [record.cost]) : ''].filter(Boolean).join(' / ') }}
                  </span>
                  <span v-else class="text-ink-gray-4">-</span>
                </td>
                <td class="px-4 py-2">
                  <div>{{ record.sync_action ? __(record.sync_action) : '-' }}</div>
                  <div v-if="record.skip_reason" class="text-p-xs text-orange-700">
                    {{ __(record.skip_reason) }}
                  </div>
                </td>
                <td class="px-4 py-2">
                  <router-link
                    v-if="record.lead"
                    :to="{ name: 'Lead', params: { leadId: record.lead } }"
                    class="text-blue-600 hover:underline"
                  >
                    {{ record.lead }}
                  </router-link>
                  <span v-else class="text-ink-gray-4">-</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div
          v-if="poiTotal > poiRecords.length"
          class="border-t px-4 py-3 text-center"
        >
          <Button
            variant="outline"
            size="sm"
            :label="__('Load more')"
            :loading="poiLoadingMore"
            @click="loadMorePoiRecords"
          />
        </div>
      </div>

      <div
        v-if="job.status === 'Completed' && job.leads_created > 0"
        class="rounded-lg border border-green-200 bg-green-50 p-4 text-p-sm text-green-800"
      >
        {{
          __(
            'Leads with phone numbers are in Pending Calls. Open Leads and switch to the Amap pending view.',
          )
        }}
      </div>

      <Dialog v-model="licenseDialogOpen" :options="{ title: __('Activate TripAI License'), size: 'sm' }">
        <template #body-content>
          <div class="space-y-3 p-1">
            <p class="text-p-sm text-ink-gray-6">
              {{ __('Enter the license key from your agent or TripAI purchase to enable POI sync.') }}
            </p>
            <FormControl
              v-model="licenseKeyInput"
              type="text"
              :label="__('License Key')"
              :placeholder="__('XXXX-XXXX-XXXX')"
            />
          </div>
        </template>
        <template #actions>
          <Button variant="solid" :label="__('Activate')" :loading="activatingLicense" @click="submitLicense" />
        </template>
      </Dialog>
    </template>
  </div>
</template>

<script setup>
import { Badge, toast, call, Dialog, FormControl, Button } from 'frappe-ui'
import { computed, inject, onBeforeUnmount, onMounted, ref } from 'vue'
import { usersStore } from '@/stores/users'
import { getUserContactDisplay } from '@/utils/userContact'
import { getTripAILicenseDeviceId, isLicenseError } from '@/utils/tripaiLicense'
import { STATUS_COLORS } from './amapConfig'

const props = defineProps({
  jobName: {
    type: String,
    required: true,
  },
})

const emit = defineEmits(['updateStep'])
const jobs = inject('poiSyncJobs')
const { getUser } = usersStore()

function ownerLabel(owner) {
  return getUserContactDisplay(getUser(owner))
}

const job = ref(null)
const loading = ref(true)
const starting = ref(false)
const cancelling = ref(false)
const licenseDialogOpen = ref(false)
const licenseKeyInput = ref('')
const activatingLicense = ref(false)
const licenseRequired = ref(false)
const licenseEntitled = ref(true)
const poiRecords = ref([])
const poiTotal = ref(0)
const poiPage = ref(1)
const poiLoading = ref(false)
const poiLoadingMore = ref(false)
let pollTimer = null

const showActivateLicense = computed(
  () => licenseRequired.value && !licenseEntitled.value && canStart.value,
)

const canStart = computed(() =>
  ['Draft', 'Completed', 'Failed', 'Cancelled'].includes(job.value?.status),
)
const canCancel = computed(() => ['Running', 'Queued'].includes(job.value?.status))

async function fetchPoiRecords(reset = false) {
  if (!props.jobName) return
  if (reset) {
    poiPage.value = 1
    poiRecords.value = []
  }

  const isFirstPage = poiPage.value === 1
  if (isFirstPage) {
    poiLoading.value = true
  } else {
    poiLoadingMore.value = true
  }

  try {
    const result = await call('crm.amap.api.list_job_poi_records', {
      job_name: props.jobName,
      page: poiPage.value,
      page_length: 20,
    })
    poiTotal.value = result?.total || 0
    const rows = result?.records || []
    poiRecords.value = reset ? rows : [...poiRecords.value, ...rows]
  } catch {
    // Non-fatal — stats cards still show progress
  } finally {
    poiLoading.value = false
    poiLoadingMore.value = false
  }
}

async function loadMorePoiRecords() {
  poiPage.value += 1
  await fetchPoiRecords(false)
}

async function fetchProgress() {
  if (!props.jobName) return
  try {
    const result = await call('crm.amap.api.get_job_progress', {
      job_name: props.jobName,
    })
    job.value = result
    if (['Running', 'Completed'].includes(result.status)) {
      await fetchPoiRecords(true)
    }
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

function formatDate(value) {
  return value || '-'
}

function phoneValues(record) {
  const values = []
  if (record.all_phones) {
    values.push(
      ...String(record.all_phones)
        .split(/\n|,|，|;|；/)
        .map((phone) => phone.trim())
        .filter(Boolean),
    )
  }
  if (record.tel_normalized) values.push(record.tel_normalized)
  if (record.tel) {
    values.push(
      ...String(record.tel)
        .split(/\n|,|，|;|；/)
        .map((phone) => phone.trim())
        .filter(Boolean),
    )
  }
  return [...new Set(values)].slice(0, 4)
}

async function loadLicenseStatus() {
  try {
    const [status, entitlement] = await Promise.all([
      call('crm.api.tripai.get_integration_status'),
      call('crm.api.tripai.get_license_status'),
    ])
    licenseRequired.value = Boolean(status?.require_license)
    licenseEntitled.value = Boolean(entitlement?.entitled ?? entitlement?.skipped)
  } catch {
    licenseRequired.value = false
    licenseEntitled.value = true
  }
}

function openLicenseDialog() {
  licenseDialogOpen.value = true
}

async function submitLicense() {
  if (!licenseKeyInput.value?.trim()) {
    toast.error(__('Please enter a license key'))
    return
  }

  activatingLicense.value = true
  try {
    await call('crm.api.tripai.activate_license_key', {
      license_key: licenseKeyInput.value.trim(),
      device_id: getTripAILicenseDeviceId(),
      device_label: __('CRM Web'),
    })
    toast.success(__('License activated'))
    licenseDialogOpen.value = false
    licenseKeyInput.value = ''
    await loadLicenseStatus()
  } catch (error) {
    toast.error(error.messages?.[0] || error.message || __('License activation failed'))
  } finally {
    activatingLicense.value = false
  }
}

async function startJob() {
  starting.value = true
  try {
    await call('crm.amap.api.start_sync_job', { job_name: props.jobName })
    toast.success(__('Sync started'))
    await fetchProgress()
  } catch (error) {
    const message = error.messages?.[0] || error.message || __('Failed to start sync')
    if (
      message.includes('Insufficient TripAI credits') ||
      message.includes('积分不足') ||
      message.includes('TripAI credits')
    ) {
      toast.error(message, {
        action: {
          label: __('Recharge'),
          onClick: openTripAIRecharge,
        },
      })
    } else if (isLicenseError(message)) {
      licenseEntitled.value = false
      toast.error(message, {
        action: {
          label: __('Activate License'),
          onClick: openLicenseDialog,
        },
      })
    } else {
      toast.error(message)
    }
  } finally {
    starting.value = false
  }
}

async function openTripAIRecharge() {
  try {
    const status = await call('crm.api.tripai.get_integration_status')
    if (status?.recharge_url) {
      window.open(status.recharge_url, '_blank', 'noopener')
    }
  } catch {
    toast.error(__('Unable to open TripAI recharge page'))
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

onMounted(async () => {
  await Promise.all([fetchProgress(), loadLicenseStatus()])
})
onBeforeUnmount(clearPoll)
</script>
