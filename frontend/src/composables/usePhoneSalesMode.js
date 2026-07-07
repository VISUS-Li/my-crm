import { computed } from 'vue'

/** Whether phone-sales simplified UI is active (from Frappe boot). */
export function usePhoneSalesMode() {
  const enabled = computed(() => Boolean(window.phone_sales_mode))

  const hiddenSidebarRoutes = [
    'Dashboard',
    'Deals',
    'Contacts',
    'Organizations',
    'Notes',
    'Calendar',
  ]

  const hiddenLeadTabs = ['Emails', 'Events', 'WhatsApp', 'Attachments']

  const hiddenSettingsLabels = [
    'Dashboard',
    'Defaults',
    'Brand',
    'Calendar',
    'Users',
    'Invite User',
    'Sales Hierarchy',
    'Accounts',
    'Templates',
    'Assignment Rules',
    'SLA Policies',
    'Home Actions',
    'Telephony',
    'WhatsApp',
    'ERPNext',
    'Lead Syncing',
    'TripAI',
    'Amap POI',
  ]

  function isSidebarRouteHidden(routeName) {
    if (!enabled.value) return false
    return hiddenSidebarRoutes.includes(routeName)
  }

  function filterLeadTabs(tabs) {
    if (!enabled.value) return tabs
    return tabs.filter((tab) => !hiddenLeadTabs.includes(tab.name))
  }

  function filterSettingsTabs(tabs) {
    if (!enabled.value) return tabs
    return tabs
      .map((tab) => ({
        ...tab,
        items: tab.items?.filter(
          (item) => !hiddenSettingsLabels.includes(item.name),
        ),
      }))
      .filter((tab) => tab.items?.length)
  }

  return {
    enabled,
    hiddenSidebarRoutes,
    hiddenLeadTabs,
    isSidebarRouteHidden,
    filterLeadTabs,
    filterSettingsTabs,
  }
}
