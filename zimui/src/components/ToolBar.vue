<script setup lang="ts">
import Topic from '@/types/Topic'
import { PropType } from 'vue'
import TagButton from '../components/TagButton.vue'

defineProps({
  topic: {
    type: Object as PropType<Topic>,
    required: true,
  },
})
</script>

<template>
  <div class="mt-2 container btn-toolbar" role="toolbar">
    <TagButton
      v-for="content in topic.sections"
      :key="content.slug"
      :data="content"
    />
  </div>
</template>

<style scoped></style>
