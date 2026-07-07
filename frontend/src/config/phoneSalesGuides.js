/**
 * Scenario-based operation guides for phone-sales / Amap POI workflow.
 * All user-visible strings are English msgids for i18n.
 */

export const PHONE_SALES_GUIDES = [
  {
    id: 'restaurant-region-outreach',
    icon: 'utensils',
    title: 'Fetch restaurant merchants in a region',
    summary:
      'Get restaurant POI data for a city or district from Amap, import merchants with phone numbers, and start calling.',
    steps: [
      {
        title: 'Confirm POI sync is ready',
        body: 'Fetch Merchants must be enabled by your administrator first. If you cannot create jobs yet, contact your admin — setup is handled on the admin side.',
        tip: 'Once enabled, you can create sync jobs and new merchant leads will appear automatically.',
      },
      {
        title: 'Create a sync job',
        body: 'Go to Fetch Merchants in the sidebar and click New Job.',
      },
      {
        title: 'Set the region',
        body: 'Fill Province, City (required), and District. Example: Zhejiang → Hangzhou → Xihu District. Narrower regions produce more relevant results.',
      },
      {
        title: 'Set industry keywords',
        body: 'In Keywords, enter terms merchants use on Amap, e.g. 餐饮, 餐厅, 饭店, 火锅. Separate multiple keywords with commas.',
        keywords: ['餐饮', '餐厅', '饭店', '火锅'],
        tip: 'Keywords match merchant names and categories on Amap. Try 餐饮 first; add 快餐 or 奶茶 if you need a sub-segment.',
      },
      {
        title: 'Import only merchants with phone numbers',
        body: 'Keep “Import only with phone” enabled (recommended). Merchants without a public phone are skipped and will not clutter your call list.',
      },
      {
        title: 'Start sync and wait',
        body: 'Save the job, then click Start Sync. Large areas may take several minutes. When status is Completed, check stats: total fetched, with phone, leads created.',
      },
      {
        title: 'Open the call list',
        body: 'Go to Pending Calls in the sidebar (or Workbench → Pending Calls card). Each row shows merchant name, phone, district, and recommended product.',
      },
      {
        title: 'Call and record the outcome',
        body: 'Open a lead → click Call. After the conversation use the quick buttons: Mark Contacted, Mark Interested, Mark Invalid, or Record Follow-up to add notes.',
      },
    ],
    actions: [
      { label: 'Fetch Merchants', type: 'route', to: { name: 'PoiSync' } },
      { label: 'Pending Calls', type: 'route', to: { name: 'Leads', params: { viewType: 'list' }, query: { view: '高德-待拨打' } } },
    ],
  },
  {
    id: 'amap-first-setup',
    icon: 'settings',
    audience: 'admin',
    title: 'First-time Amap API setup',
    summary: 'Connect your Amap developer account so the system can fetch merchant POI data.',
    steps: [
      {
        title: 'Get an Amap API key',
        body: 'Register at Amap Open Platform (lbs.amap.com), create an application, and enable the Web Service / Place Search API. Copy the API key.',
      },
      {
        title: 'Add the key in CRM',
        body: 'Settings → Amap POI → API Keys table → add a row with your key. Enable “Amap POI Sync”.',
      },
      {
        title: 'Set defaults',
        body: 'Choose Default Lead Owner and Default Product. New POI leads inherit these automatically.',
        tip: 'Default product helps sales know which offering to introduce on the first call.',
      },
      {
        title: 'Test the connection',
        body: 'Click Test Connection on the settings page. If it succeeds, you are ready to create sync jobs.',
      },
    ],
    actions: [{ label: 'Open Amap Settings', type: 'settings', page: 'Amap POI' }],
  },
  {
    id: 'call-pending-leads',
    icon: 'phone',
    title: 'Start calling pending merchants',
    summary: 'Work through the Pending Calls list and contact merchants one by one.',
    steps: [
      {
        title: 'Open Pending Calls',
        body: 'Sidebar → Pending Calls. The list is filtered to Amap leads with a valid phone and status “Pending Call”.',
      },
      {
        title: 'Pick a merchant',
        body: 'Click a row to open the lead detail. Confirm phone, address, POI type, and recommended product on the right panel.',
      },
      {
        title: 'Make the call',
        body: 'Click the Call button next to the phone number. If telephony is configured, the call starts in-browser; otherwise use your phone and dial the number shown.',
      },
      {
        title: 'Update status immediately',
        body: 'After hanging up: Mark Contacted if you spoke; Mark Invalid if wrong number or not a fit; Mark Interested if they want to learn more.',
        tip: 'Do not leave status as Pending Call after you dial — it keeps your queue accurate for the team.',
      },
      {
        title: 'Add a follow-up note',
        body: 'Click Record Follow-up to log what was said, objections, and next steps. Notes appear in the Activity timeline.',
      },
    ],
    actions: [
      {
        label: 'Open Pending Calls',
        type: 'route',
        to: { name: 'Leads', params: { viewType: 'list' }, query: { view: '高德-待拨打' } },
      },
    ],
  },
  {
    id: 'mark-follow-up',
    icon: 'clipboard',
    title: 'Record call outcomes and notes',
    summary: 'Keep every call traceable with status changes and follow-up notes.',
    steps: [
      {
        title: 'Use quick action buttons',
        body: 'On an Amap lead detail page, use: Mark Contacted, Mark Interested, Mark Invalid, Record Follow-up. These appear for leads imported from Amap.',
      },
      {
        title: 'Status meanings',
        body: 'Pending Call = not yet dialed. Contacted = spoke but no clear interest. Interested = wants demo or quote. Invalid = bad number or not target. No Answer = try again later.',
      },
      {
        title: 'Write useful notes',
        body: 'In Record Follow-up, note: who you spoke with, current tools, pain points, agreed next step, and best time to call back.',
      },
      {
        title: 'Create a task for callbacks',
        body: 'If the merchant asked to be called back, create a Task with due date from the lead’s Tasks tab so you do not forget.',
      },
    ],
    actions: [
      {
        label: 'Contacted Today',
        type: 'route',
        to: { name: 'Leads', params: { viewType: 'list' }, query: { view: '高德-今日已联系' } },
      },
    ],
  },
  {
    id: 'interested-follow-up',
    icon: 'star',
    title: 'Follow up interested merchants',
    summary: 'Move warm leads toward demo, trial, or closing your product.',
    steps: [
      {
        title: 'Open the Interested list',
        body: 'Sidebar → Interested, or Workbench → Interested card. These leads already showed buying intent.',
      },
      {
        title: 'Review history first',
        body: 'Read Activity and Comments before calling again so you continue the conversation naturally.',
      },
      {
        title: 'Advance the status',
        body: 'After scheduling a demo, set status to Demo/Trial. After sending pricing, set to Quote. Update recommended product if pitching a different offering.',
      },
      {
        title: 'Set reminders',
        body: 'Create Tasks for demo dates and follow-up calls. Use Call Logs to record each conversation.',
      },
    ],
    actions: [
      {
        label: 'Open Interested',
        type: 'route',
        to: { name: 'Leads', params: { viewType: 'list' }, query: { view: '高德-有意向' } },
      },
    ],
  },
]

export function getGuideById(id) {
  return PHONE_SALES_GUIDES.find((guide) => guide.id === id) || null
}

export function getGuideList(options = {}) {
  const { audience } = options
  if (!audience) return PHONE_SALES_GUIDES
  return PHONE_SALES_GUIDES.filter(
    (guide) => (guide.audience || 'user') === audience,
  )
}
