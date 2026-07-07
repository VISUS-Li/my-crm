<template>
  <LeadPhotoGallery
    v-if="photos.data?.length"
    :photos="photos.data"
    class="border-b px-5 py-4"
  />
</template>

<script setup>
import LeadPhotoGallery from '@/components/Leads/LeadPhotoGallery.vue'
import { createResource } from 'frappe-ui'

const props = defineProps({
  leadId: { type: String, required: true },
})

const photos = createResource({
  url: 'crm.api.lead_media.get_lead_photos',
  params: { lead_name: props.leadId },
  auto: true,
  transform(data) {
    return data || []
  },
})

defineExpose({
  reload: () => photos.reload(),
})
</script>
