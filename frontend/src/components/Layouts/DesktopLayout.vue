<template>
  <div class="flex h-screen w-screen">
    <div class="h-full border-r bg-surface-gray-1">
      <AppSidebar />
    </div>
    <div class="flex min-h-0 flex-1 flex-col bg-surface-base">
      <AppHeader class="shrink-0" />
      <div class="min-h-0 flex-1 overflow-auto">
        <slot />
      </div>
    </div>
    <GlobalModals />
  </div>
</template>
<script setup>
import AppSidebar from '@/components/Layouts/AppSidebar.vue'
import AppHeader from '@/components/Layouts/AppHeader.vue'
import GlobalModals from '@/components/Modals/GlobalModals.vue'
</script>
