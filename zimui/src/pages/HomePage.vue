<script setup lang="ts">
import { onMounted, toRef, Ref, ref, watch } from 'vue'
import { RouteParams, useRoute } from 'vue-router'

import { useMainStore } from '../stores/main'
const main = useMainStore()

const route = useRoute()
const params: Ref<RouteParams> = toRef(route, 'params')
const topic: Ref<string> = ref(params.value.topic as string)

// update topic when route params are changed
watch(params, () => {
  topic.value = params.value.topic as string
  if (topic.value === undefined && main.channelData != null) {
    topic.value = main.channelData.rootSlug
  }
})

// fetch channel data and set default topic if needed
onMounted(async () => {
  try {
    await main.fetchChannel()
    if (topic.value === undefined && main.channelData != null) {
      topic.value = main.channelData.rootSlug
    }
  } catch (error) {
    main.setErrorMessage('An unexpected error occured.')
  }
})

import TopicHome from '../components/TopicHome.vue'
import ErrorDisplay from '@/components/ErrorDisplay.vue'
</script>

<template>
  <div v-if="main.errorMessage">
    <ErrorDisplay />
  </div>
  <div v-else class="d-flex flex-column h-100">
    <div class="flex-fill flex-shrink-0">
      <TopicHome v-if="main.channelData" :slug="topic" />
    </div>
  </div>
</template>

<style scoped></style>
