<template>
  <div class="flex h-full flex-col overflow-hidden">
    <LayoutHeader>
      <template #left-header>
        <div class="text-2xl-semibold text-ink-gray-9">{{ __('Workbench') }}</div>
      </template>
      <template #right-header>
        <Button
          variant="outline"
          :label="__('Operation Guides')"
          icon-left="book-open"
          @click="scrollToGuides"
        />
        <Button
          variant="solid"
          :label="__('Fetch Merchants')"
          icon-left="map-pin"
          @click="router.push({ name: 'PoiSync' })"
        />
      </template>
    </LayoutHeader>

    <div class="flex-1 overflow-y-auto p-5">
      <div
        v-if="stats.loading"
        class="flex h-48 items-center justify-center text-ink-gray-5"
      >
        <LoadingIndicator class="h-6 w-6" />
      </div>

      <template v-else>
        <GuideInfoBanner
          v-if="showQuickTip"
          :title="__('New here? Start with a scenario guide below')"
          :description="
            __(
              'For example: fetch restaurant merchants in your city, get their phone numbers, and start calling — each guide walks you through every click.',
            )
          "
          guide-id="restaurant-region-outreach"
        />

        <ScenarioGuideSection />

        <!-- Stats cards -->
        <div class="mb-6 mt-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
          <StatCard
            :label="__('Pending Calls')"
            :value="stats.data?.pending_call ?? 0"
            theme="orange"
            icon="phone"
            @click="goToView('高德-待拨打')"
          />
          <StatCard
            :label="__('Contacted Today')"
            :value="stats.data?.contacted_today ?? 0"
            theme="cyan"
            icon="check"
            @click="goToView('高德-今日已联系')"
          />
          <StatCard
            :label="__('Interested')"
            :value="stats.data?.interested ?? 0"
            theme="green"
            icon="star"
            @click="goToView('高德-有意向')"
          />
          <StatCard
            :label="__('New Leads')"
            :value="stats.data?.new_leads ?? 0"
            theme="blue"
            icon="map-pin"
            @click="goToView('高德-新线索')"
          />
        </div>

        <!-- Primary action -->
        <div
          v-if="(stats.data?.pending_call ?? 0) > 0"
          class="mb-6 flex items-center justify-between rounded-xl border bg-surface-elevation-2 p-5"
        >
          <div>
            <div class="text-lg-semibold text-ink-gray-9">
              {{
                __('{0} merchants waiting for your call', [
                  stats.data.pending_call,
                ])
              }}
            </div>
            <div class="mt-1 text-p-base text-ink-gray-6">
              {{ __('Start with the first one in the list') }}
            </div>
          </div>
          <div class="flex gap-2">
            <Button
              variant="outline"
              :label="__('How to call')"
              icon-left="book-open"
              @click="openPhoneSalesGuide('call-pending-leads')"
            />
            <Button
              variant="solid"
              size="lg"
              :label="__('Start Calling')"
              icon-left="phone"
              @click="goToView('高德-待拨打')"
            />
          </div>
        </div>

        <!-- Recent sync jobs -->
        <div class="rounded-xl border bg-surface-elevation-2">
          <div
            class="flex items-center justify-between border-b px-5 py-3 text-lg-semibold text-ink-gray-9"
          >
            <span>{{ __('Recent POI Sync Jobs') }}</span>
            <Button
              variant="ghost"
              :label="__('View All')"
              @click="router.push({ name: 'PoiSync' })"
            />
          </div>
          <div v-if="!stats.data?.recent_jobs?.length" class="p-8 text-center">
            <EmptyState
              :name="__('POI Sync Jobs')"
              :description="
                __(
                  'No sync jobs yet. Create one to fetch merchant data from Amap.',
                )
              "
              icon="map-pin"
            />
            <Button
              class="mt-4"
              variant="outline"
              :label="__('View setup guide')"
              icon-left="book-open"
              @click="openPhoneSalesGuide('amap-first-setup')"
            />
          </div>
          <div v-else class="divide-y">
            <div
              v-for="job in stats.data.recent_jobs"
              :key="job.name"
              class="flex cursor-pointer items-center justify-between px-5 py-3 hover:bg-surface-gray-1"
              @click="router.push({ name: 'PoiSync' })"
            >
              <div>
                <div class="text-p-base-medium text-ink-gray-9">
                  {{ job.keywords }} · {{ job.city
                  }}{{ job.district ? ` / ${job.district}` : '' }}
                </div>
                <div class="mt-0.5 text-p-sm text-ink-gray-5">
                  {{
                    __('Fetched {0}, {1} with phone, {2} leads created', [
                      job.total_fetched || 0,
                      job.with_phone_count || 0,
                      job.leads_created || 0,
                    ])
                  }}
                </div>
              </div>
              <Badge :label="__(job.status)" variant="subtle" />
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import StatCard from '@/components/Workbench/StatCard.vue'
import ScenarioGuideSection from '@/components/Workbench/ScenarioGuideSection.vue'
import GuideInfoBanner from '@/components/Workbench/GuideInfoBanner.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import { openPhoneSalesGuide } from '@/composables/usePhoneSalesGuide'
import { createResource, Button, Badge, LoadingIndicator } from 'frappe-ui'
import { computed, nextTick, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

const stats = createResource({
  url: 'crm.api.phone_sales.get_workbench_stats',
  auto: true,
})

const showQuickTip = computed(() => {
  const data = stats.data
  if (!data) return false
  return !data.has_amap_enabled || (data.pending_call ?? 0) === 0
})

function goToView(viewName) {
  router.push({
    name: 'Leads',
    params: { viewType: 'list' },
    query: { view: viewName },
  })
}

function scrollToGuides() {
  document
    .getElementById('operation-guides')
    ?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

onMounted(async () => {
  if (route.hash === '#operation-guides') {
    await nextTick()
    scrollToGuides()
  }
})
</script>
