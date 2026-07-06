<template>
  <Dialog
    v-model:open="showSettings"
    :size="'5xl'"
    :disableOutsideClickToClose="disableSettingModalOutsideClick"
    @close="activeSettingsPage = ''"
  >
    <template #body>
      <div class="flex h-[calc(100vh_-_8rem)] bg-surface-gray-1">
        <div
          class="flex flex-col m-1 rounded-l-lg w-56 shrink-0 bg-surface-gray-1 overflow-y-auto"
        >
          <template v-for="(tab, i) in tabs" :key="tab.label">
            <div v-if="!tab.hideLabel && i != 0" class="mx-1 mb-0.5 mt-[5px]" />
            <div
              v-if="!tab.hideLabel"
              class="h-7.5 px-2 py-[7px] my-[3px] flex cursor-pointer gap-1.5 text-xs-medium text-ink-gray-5 transition-all duration-300 ease-in-out sticky top-0 z-10 bg-surface-gray-1"
            >
              <span>{{ __(tab.label) }}</span>
            </div>
            <nav class="space-y-[3px] px-1">
              <SidebarLink
                v-for="item in tab.items"
                :key="item.name"
                :icon="item.icon"
                :label="__(item.label)"
                class="w-full"
                :class="
                  activeTab?.name == item.name
                    ? 'bg-surface-elevation-3 shadow-sm hover:bg-surface-elevation-3'
                    : 'hover:bg-surface-gray-3'
                "
                @click="activeSettingsPage = item.name"
              />
            </nav>
          </template>
        </div>
        <div
          class="flex flex-col flex-1 overflow-y-auto bg-surface-elevation-2"
        >
          <component :is="activeTab.component" v-if="activeTab" />
        </div>
      </div>
    </template>
  </Dialog>
</template>
<script setup>
import LucideLayoutDashboard from '~icons/lucide/layout-dashboard'
import LucideNetwork from '~icons/lucide/network'
import MonitorCogIcon from '~icons/lucide/monitor-cog'
import SlidersIcon from '@/components/Icons/SlidersIcon.vue'
import SparkleIcon from '@/components/Icons/SparkleIcon.vue'
import CalendarIcon from '@/components/Icons/CalendarIcon.vue'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import ERPNextIcon from '@/components/Icons/ERPNextIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import EmailTemplateIcon from '@/components/Icons/EmailTemplateIcon.vue'
import SettingsIcon from '@/components/Icons/SettingsIcon.vue'
import SettingsIcon2 from '@/components/Icons/SettingsIcon2.vue'
import Users from '@/components/Settings/Users.vue'
import Hierarchy from '@/components/Settings/Hierarchy/Hierarchy.vue'
import InviteUserPage from '@/components/Settings/InviteUserPage.vue'
import ProfilePage from '@/components/Settings/Profile/ProfilePage.vue'
import PreferencesSettings from '@/components/Settings/PreferencesSettings.vue'
import WhatsAppSettings from '@/components/Settings/WhatsAppSettings.vue'
import ERPNextSettings from '@/components/Settings/ERPNextSettings.vue'
import LeadSyncSourcePage from '@/components/Settings/LeadSyncing/LeadSyncSourcePage.vue'
import AmapPage from '@/components/Settings/Amap/AmapPage.vue'
import TripAIPage from '@/components/Settings/TripAI/TripAIPage.vue'
import DefaultsSettings from '@/components/Settings/DefaultsSettings.vue'
import BrandSettings from '@/components/Settings/BrandSettings.vue'
import CalendarSettings from '@/components/Settings/CalendarSettings.vue'
import HomeActions from '@/components/Settings/HomeActions.vue'
import GeneralSettings from '@/components/Settings/GeneralSettings.vue'
import DashboardSettings from '@/components/Settings/DashboardSettings.vue'
import EmailTemplatePage from '@/components/Settings/EmailTemplate/EmailTemplatePage.vue'
import TelephonyPage from '@/components/Settings/Telephony/TelephonyPage.vue'
import EmailConfig from '@/components/Settings/EmailConfig.vue'
import SidebarLink from '@/components/SidebarLink.vue'
import { usersStore } from '@/stores/users'
import {
  showSettings,
  activeSettingsPage,
  disableSettingModalOutsideClick,
} from '@/composables/settings'
import { isWhatsappInstalled } from '@/composables/whatsapp'
import { Dialog, Avatar } from 'frappe-ui'
import { ref, markRaw, computed, watch, h } from 'vue'
import { usePhoneSalesMode } from '@/composables/usePhoneSalesMode'
import AssignmentRulePage from './AssignmentRules/AssignmentRulePage.vue'
import ShieldCheck from '~icons/lucide/shield-check'
import SlaConfig from './Sla/SlaConfig.vue'

const { isManager, getUser } = usersStore()
const { filterSettingsTabs, enabled: phoneSalesMode } = usePhoneSalesMode()

const user = computed(() => getUser() || {})

const tabs = computed(() => {
  let _tabs = [
    {
      label: 'User Configuration',
      items: [
        {
          name: 'Profile',
          label: 'Profile',
          icon: () =>
            h(Avatar, {
              size: 'xs',
              label: user.value.full_name,
              image: user.value.user_image,
            }),
          component: markRaw(ProfilePage),
        },
        {
          name: 'Preferences',
          label: 'Preferences',
          icon: SlidersIcon,
          component: markRaw(PreferencesSettings),
        },
      ],
    },
    {
      label: 'System Configuration',
      items: [
        {
          name: 'General',
          label: 'General',
          component: markRaw(GeneralSettings),
          icon: SettingsIcon,
        },
        {
          name: 'Dashboard',
          label: 'Dashboard',
          component: markRaw(DashboardSettings),
          icon: LucideLayoutDashboard,
        },
        {
          name: 'Defaults',
          label: 'Defaults',
          component: markRaw(DefaultsSettings),
          icon: MonitorCogIcon,
        },
        {
          name: 'Brand',
          label: 'Brand',
          icon: SparkleIcon,
          component: markRaw(BrandSettings),
        },
        {
          name: 'Calendar',
          label: 'Calendar',
          icon: CalendarIcon,
          component: markRaw(CalendarSettings),
        },
      ],
      condition: () => isManager(),
    },
    {
      label: 'User Management',
      items: [
        {
          name: 'Users',
          label: 'Users',
          icon: 'user',
          component: markRaw(Users),
          condition: () => isManager(),
        },
        {
          name: 'Invite User',
          label: 'Invite User',
          icon: 'user-plus',
          component: markRaw(InviteUserPage),
          condition: () => isManager(),
        },
        {
          name: 'Sales Hierarchy',
          label: 'Sales Hierarchy',
          icon: LucideNetwork,
          component: markRaw(Hierarchy),
          condition: () => isManager(),
        },
      ],
      condition: () => isManager(),
    },
    {
      label: 'Email',
      items: [
        {
          name: 'Accounts',
          label: 'Accounts',
          icon: Email2Icon,
          component: markRaw(EmailConfig),
          condition: () => isManager(),
        },
        {
          name: 'Templates',
          label: 'Templates',
          icon: EmailTemplateIcon,
          component: markRaw(EmailTemplatePage),
        },
      ],
    },
    {
      label: 'Automation & Rules',
      items: [
        {
          name: 'Assignment Rules',
          label: 'Assignment Rules',
          icon: markRaw(h(SettingsIcon2, { class: 'rotate-90' })),
          component: markRaw(AssignmentRulePage),
        },
        {
          name: 'SLA Policies',
          label: 'SLA Policies',
          icon: markRaw(h(ShieldCheck)),
          component: markRaw(SlaConfig),
        },
      ],
      condition: () => isManager(),
    },
    {
      label: 'Customization',
      items: [
        {
          name: 'Home Actions',
          label: 'Home Actions',
          component: markRaw(HomeActions),
          icon: 'home',
        },
      ],
      condition: () => isManager(),
    },
    {
      label: 'Integrations',
      items: [
        {
          name: 'Telephony',
          label: 'Telephony',
          icon: PhoneIcon,
          component: markRaw(TelephonyPage),
        },
        {
          name: 'WhatsApp',
          label: 'WhatsApp',
          icon: WhatsAppIcon,
          component: markRaw(WhatsAppSettings),
          condition: () => isWhatsappInstalled.value && isManager(),
        },
        {
          name: 'ERPNext',
          label: 'ERPNext',
          icon: ERPNextIcon,
          component: markRaw(ERPNextSettings),
          condition: () => isManager(),
        },
        {
          name: 'Lead Syncing',
          label: 'Lead Syncing',
          icon: 'refresh-cw',
          component: markRaw(LeadSyncSourcePage),
          condition: () => isManager(),
        },
        {
          name: 'Amap POI',
          label: 'Amap POI',
          icon: 'map-pin',
          component: markRaw(AmapPage),
        },
        {
          name: 'TripAI',
          label: 'TripAI',
          icon: 'link',
          component: markRaw(TripAIPage),
          condition: () => isManager(),
        },
      ],
    },
  ]

  return filterSettingsTabs(
    _tabs.filter((tab) => {
      if (tab.condition && !tab.condition()) return false
      if (tab.items) {
        tab.items = tab.items.filter((item) => {
          if (item.condition && !item.condition()) return false
          return true
        })
      }
      return true
    }),
  )
})

const activeTab = ref(tabs.value[0].items[0])

function setActiveTab(tabName) {
  activeTab.value =
    (tabName &&
      tabs.value
        .map((tab) => tab.items)
        .flat()
        .find((tab) => tab.name === tabName)) ||
    tabs.value[0].items[0]
}

watch(activeSettingsPage, (activePage) => setActiveTab(activePage))
</script>
