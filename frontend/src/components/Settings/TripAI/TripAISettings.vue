<template>
  <SettingsLayoutBase>
    <template #title>
      <h2 class="text-2xl-semibold">{{ __('TripAI Settings') }}</h2>
    </template>
    <template #header-actions>
      <div class="flex gap-2">
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
        <div class="rounded-lg border border-blue-100 bg-blue-50 p-4 text-p-sm text-blue-900">
          {{
            __(
              'CRM login authenticates via TripAI on the server side. Set the URL that the CRM backend can reach — e.g. your dev machine http://10.0.160.64:3000 or server-local http://127.0.0.1:23000.',
            )
          }}
        </div>

        <div class="flex items-center justify-between rounded-lg border p-4">
          <div>
            <div class="text-base-medium">{{ __('Enable TripAI Integration') }}</div>
            <div class="text-p-sm text-ink-gray-5">
              {{ __('Required for TripAI login, licenses, and POI sync billing') }}
            </div>
          </div>
          <Switch v-model="settings.doc.enabled" size="sm" />
        </div>

        <div class="grid grid-cols-2 gap-4">
          <FormControl
            v-model="settings.doc.base_url"
            type="text"
            :label="__('TripAI Base URL')"
            :placeholder="__('http://10.0.160.64:3000')"
            required
          />
          <FormControl
            v-model="settings.doc.default_redirect_path"
            type="text"
            :label="__('Default Redirect Path')"
            :placeholder="'/crm'"
          />
        </div>

        <div class="grid grid-cols-2 gap-4">
          <FormControl
            v-model="settings.doc.project_key"
            type="text"
            :label="__('Project Key')"
            required
          />
          <FormControl
            v-model="settings.doc.tool_key"
            type="text"
            :label="__('Tool Key')"
            required
          />
        </div>

        <Password
          v-model="settings.doc.runtime_token"
          :label="__('Runtime Token')"
          :placeholder="__('********')"
        />

        <div class="flex items-center gap-2">
          <Switch v-model="settings.doc.require_license" size="sm" />
          <span class="text-p-sm">{{ __('Require TripAI License for POI Sync') }}</span>
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
import { Switch, toast, call } from 'frappe-ui'
import { computed, ref } from 'vue'
import { TRIPAI_SETTINGS_DOCTYPE } from './tripaiConfig'

const testing = ref(false)

const { document: settings } = useDocument(
  TRIPAI_SETTINGS_DOCTYPE,
  TRIPAI_SETTINGS_DOCTYPE,
)

const isDirty = computed(() => settings.isDirty?.value ?? settings.isDirty)

async function saveSettings() {
  await settings.save.submit()
  toast.success(__('Settings saved'))
}

async function testConnection() {
  testing.value = true
  try {
    if (isDirty.value) {
      await settings.save.submit()
    }
    const result = await call('crm.api.tripai.test_connection')
    if (result?.success) {
      toast.success(__(result.message) || __('Connection successful'))
    } else {
      toast.error(__(result.message) || __('Connection failed'))
    }
  } catch (error) {
    toast.error(error.messages?.[0] || error.message || __('Connection failed'))
  } finally {
    testing.value = false
  }
}
</script>
