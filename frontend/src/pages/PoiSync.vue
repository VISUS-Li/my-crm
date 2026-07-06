<template>
  <div class="flex h-full flex-col overflow-hidden">
    <LayoutHeader>
      <template #left-header>
        <div>
          <div class="text-2xl-semibold text-ink-gray-9">
            {{ __('Fetch Merchants') }}
          </div>
          <p class="mt-0.5 text-p-sm text-ink-gray-6">
            {{
              __(
                'Pull merchant POI data from Amap by region and industry. Leads with phone numbers are created automatically.',
              )
            }}
          </p>
        </div>
      </template>
      <template #right-header>
        <Button
          variant="outline"
          :label="__('Operation Guides')"
          icon-left="book-open"
          @click="openPhoneSalesGuide('restaurant-region-outreach')"
        />
      </template>
    </LayoutHeader>

    <div class="shrink-0 px-5 pt-4">
      <GuideInfoBanner
        :title="__('Example: restaurants in your city')"
        :description="
          __(
            'Set city + district + keyword 餐饮 to fetch local restaurants with phone numbers, then call from Pending Calls.',
          )
        "
        guide-id="restaurant-region-outreach"
      />
    </div>

    <AmapPage class="min-h-0 flex-1 overflow-hidden" />
  </div>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import GuideInfoBanner from '@/components/Workbench/GuideInfoBanner.vue'
import AmapPage from '@/components/Settings/Amap/AmapPage.vue'
import { openPhoneSalesGuide } from '@/composables/usePhoneSalesGuide'
import { Button } from 'frappe-ui'
</script>
