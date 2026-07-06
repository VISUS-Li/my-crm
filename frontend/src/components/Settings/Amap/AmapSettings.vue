<template>
  <SettingsLayoutBase>
    <template #title>
      <div class="flex gap-2 items-center">
        <h2 class="text-2xl-semibold">{{ __('Amap Settings') }}</h2>
        <Badge v-if="settings.doc?.use_mock_api" theme="orange" size="sm">
          {{ __('Mock Mode') }}
        </Badge>
      </div>
    </template>
    <template #header-actions>
      <div class="flex gap-2">
        <Button
          variant="outline"
          :label="__('Back to Jobs')"
          icon-left="lucide-list"
          @click="emit('updateStep', 'job-list')"
        />
        <Button
          variant="outline"
          :label="__('Test Connection')"
          :loading="testing"
          @click="testConnection"
        />
        <Button
          variant="solid"
          :label="__('Save')"
          :loading="settings.save.loading"
          :disabled="!isDirty"
          @click="saveSettings"
        />
      </div>
    </template>
    <template #content>
      <div v-if="settings.doc" class="space-y-6">
        <div class="grid grid-cols-2 gap-4">
          <div class="flex items-center justify-between rounded-lg border p-4">
            <div>
              <div class="text-base-medium">{{ __('Enable Amap POI Sync') }}</div>
              <div class="text-p-sm text-ink-gray-5">
                {{ __('Turn on POI collection for all agents') }}
              </div>
            </div>
            <Switch v-model="settings.doc.enabled" size="sm" />
          </div>
          <div class="flex items-center justify-between rounded-lg border p-4">
            <div>
              <div class="text-base-medium">{{ __('Use Mock API') }}</div>
              <div class="text-p-sm text-ink-gray-5">
                {{ __('Test the full flow without Amap API keys') }}
              </div>
            </div>
            <Switch v-model="settings.doc.use_mock_api" size="sm" />
          </div>
        </div>

        <div class="grid grid-cols-3 gap-4">
          <FormControl
            v-model="settings.doc.request_interval"
            type="number"
            :label="__('Request Interval (s)')"
          />
          <FormControl
            v-model="settings.doc.poi_threshold"
            type="number"
            :label="__('POI Threshold')"
          />
          <FormControl
            v-model="settings.doc.max_recursion_depth"
            type="number"
            :label="__('Max Recursion Depth')"
          />
        </div>

        <div class="grid grid-cols-2 gap-4">
          <FormControl
            v-model="settings.doc.default_lead_owner"
            type="link"
            doctype="User"
            :label="__('Default Lead Owner')"
          />
          <FormControl
            v-model="settings.doc.default_product"
            type="link"
            doctype="CRM Product"
            :label="__('Default Product')"
          />
        </div>

        <div class="flex items-center gap-2">
          <Switch v-model="settings.doc.import_only_with_phone" size="sm" />
          <span class="text-p-sm">{{ __('Import only POIs with valid phone') }}</span>
        </div>

        <div class="space-y-3">
          <div class="flex items-center justify-between">
            <h3 class="text-lg-medium">{{ __('API Keys') }}</h3>
            <Button
              variant="outline"
              size="sm"
              icon-left="lucide-plus"
              :label="__('Add Key')"
              @click="addApiKey"
            />
          </div>
          <div
            v-if="!settings.doc.api_keys?.length"
            class="rounded-lg border border-dashed p-6 text-p-sm text-ink-gray-5"
          >
            {{ __('No API keys configured. Enable mock mode or add keys here.') }}
          </div>
          <div class="rounded-lg border border-blue-100 bg-blue-50 p-4 text-p-sm text-blue-900">
            {{
              __(
                'Use Amap Web Service API Key (not JS API / Android / iOS). Add server IP to the key whitelist on Amap console. Save before testing if you changed other settings.',
              )
            }}
          </div>
          <div
            v-for="(row, index) in settings.doc.api_keys"
            :key="index"
            class="grid grid-cols-[1fr_1fr_auto] gap-3 rounded-lg border p-4"
          >
            <Password
              v-model="row.api_key"
              :label="__('API Key')"
              :placeholder="__('********')"
            />
            <FormControl
              v-model="row.remark"
              type="text"
              :label="__('Remark')"
            />
            <Button
              variant="ghost"
              icon="trash-2"
              class="self-end"
              @click="removeApiKey(index)"
            />
          </div>
        </div>
      </div>
      <div v-else class="flex items-center justify-center mt-[35%]">
        <LoadingIndicator class="size-6" />
      </div>
    </template>
  </SettingsLayoutBase>
</template>

<script setup>
import SettingsLayoutBase from '@/components/Layouts/SettingsLayoutBase.vue'
import { useDocument } from '@/data/document'
import { Badge, Switch, toast, call } from 'frappe-ui'
import { computed, ref } from 'vue'
import { AMAP_SETTINGS_DOCTYPE } from './amapConfig'

const emit = defineEmits(['updateStep'])

const testing = ref(false)

const { document: settings } = useDocument(
  AMAP_SETTINGS_DOCTYPE,
  AMAP_SETTINGS_DOCTYPE,
)

const isDirty = computed(() => settings.isDirty?.value ?? settings.isDirty)

function addApiKey() {
  settings.doc.api_keys = settings.doc.api_keys || []
  settings.doc.api_keys.push({ api_key: '', remark: '' })
}

function removeApiKey(index) {
  settings.doc.api_keys.splice(index, 1)
}

async function saveSettings() {
  await settings.save.submit()
  toast.success(__('Settings saved'))
}

async function testConnection() {
  if (settings.doc.use_mock_api) {
    testing.value = true
    try {
      const result = await call('crm.amap.api.test_connection')
      if (result?.success) {
        toast.success(__(result.message) || __('Connection successful'))
      } else {
        toast.error(__(result.message) || __('Connection failed'))
      }
    } catch (error) {
      toast.error(error.messages?.[0] || __('Connection failed'))
    } finally {
      testing.value = false
    }
    return
  }

  const apiKeyFromForm =
    settings.doc.api_keys?.map((row) => row.api_key).find(Boolean) || ''
  const hasSavedKeyRows = (settings.doc.api_keys?.length || 0) > 0

  if (!apiKeyFromForm && !hasSavedKeyRows) {
    toast.error(__('Please add a Web Service API Key first'))
    return
  }

  testing.value = true
  try {
    if (isDirty.value) {
      await settings.save.submit()
    }
    const result = await call(
      'crm.amap.api.test_connection',
      apiKeyFromForm ? { api_key: apiKeyFromForm } : {},
    )
    if (result?.success) {
      toast.success(__(result.message) || __('Connection successful'))
      } else {
        toast.error(__(result.message) || __('Connection failed'))
    }
  } catch (error) {
    toast.error(error.messages?.[0] || __('Connection failed'))
  } finally {
    testing.value = false
  }
}
</script>
