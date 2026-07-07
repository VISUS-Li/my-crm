import LucideLayoutDashboard from '~icons/lucide/layout-dashboard'
import LucideMapPin from '~icons/lucide/map-pin'
import LucideStar from '~icons/lucide/star'
import LucidePhoneCall from '~icons/lucide/phone-call'
import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import OrganizationsIcon from '@/components/Icons/OrganizationsIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import CalendarIcon from '@/components/Icons/CalendarIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'

/** Standard TripAI CRM sidebar links. */
export const standardSidebarLinks = [
  { label: 'Dashboard', icon: LucideLayoutDashboard, to: 'Dashboard' },
  { label: 'Leads', icon: LeadsIcon, to: 'Leads' },
  { label: 'Deals', icon: DealsIcon, to: 'Deals' },
  { label: 'Contacts', icon: ContactsIcon, to: 'Contacts' },
  { label: 'Organizations', icon: OrganizationsIcon, to: 'Organizations' },
  { label: 'Notes', icon: NoteIcon, to: 'Notes' },
  { label: 'Tasks', icon: TaskIcon, to: 'Tasks' },
  { label: 'Calendar', icon: CalendarIcon, to: 'Calendar' },
  { label: 'Call Logs', icon: PhoneIcon, to: 'Call Logs' },
]

/** Phone-sales mode: focused menu for Amap POI + outbound calling workflow. */
export const phoneSalesSidebarLinks = [
  {
    label: 'Workbench',
    icon: LucideLayoutDashboard,
    to: 'Workbench',
  },
  {
    label: 'Pending Calls',
    icon: LucidePhoneCall,
    to: {
      name: 'Leads',
      params: { viewType: 'list' },
      query: { view: '高德-待拨打' },
    },
  },
  {
    label: 'Interested',
    icon: LucideStar,
    to: {
      name: 'Leads',
      params: { viewType: 'list' },
      query: { view: '高德-有意向' },
    },
  },
  {
    label: 'Leads',
    icon: LeadsIcon,
    to: 'Leads',
  },
  {
    label: 'Fetch Merchants',
    icon: LucideMapPin,
    to: 'PoiSync',
  },
  {
    label: 'Call Logs',
    icon: PhoneIcon,
    to: 'Call Logs',
  },
  {
    label: 'Tasks',
    icon: TaskIcon,
    to: 'Tasks',
  },
]

export function getSidebarLinks(phoneSalesMode) {
  return phoneSalesMode ? phoneSalesSidebarLinks : standardSidebarLinks
}
