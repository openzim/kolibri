<script setup lang="ts">
import { onMounted, toRef, Ref, ref, watch } from 'vue'
import { RouteParams, useRoute } from 'vue-router'

import { useMainStore } from '../stores/main'
const main = useMainStore()

const route = useRoute()
const params: Ref<RouteParams> = toRef(route, 'params')
const topic: Ref<string> = ref(params.value.topic as string)

const fetchData = async function () {
  await main.fetchChannel()
  topic.value = params.value.topic as string
  if (topic.value === undefined && main.channel_data != null) {
    topic.value = main.channel_data['root']
  }
}

watch(params, fetchData)

onMounted(() => {
  fetchData()
})

import TopicHome from '../components/TopicHome.vue'
</script>

<template>
  <div class="d-flex flex-column h-100">
    <div class="flex-fill flex-shrink-0">
      <TopicHome v-if="main.channel_data" :slug="topic" />
    </div>
  </div>
</template>

<style scoped></style>
