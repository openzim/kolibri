<script setup lang="ts">
import { onMounted } from 'vue'
import { Tooltip } from 'bootstrap'
defineProps({
  data: {
    type: Object,
    required: true,
  },
})

onMounted(() => {
  //initialize tooltip
  const tooltipTriggerList = document.querySelectorAll(
    '[data-toggle="tooltip"]',
  )
  tooltipTriggerList.forEach(function (tooltipTriggerEl) {
    const tooltip = new Tooltip(tooltipTriggerEl, {
      trigger: 'hover',
    })
    tooltipTriggerEl.addEventListener('click', () => {
      tooltip.dispose()
    })
  })
})
</script>

<template>
  <div>
    <router-link class="text-decoration-none text-reset" :to="`./${data.slug}`">
      <div role="group" class="mx-1 mt-1 btn-group btn-group-sm">
        <button
          type="button"
          class="btn btn-primary btn-sm rounded-pill tagbutton"
          data-toggle="tooltip"
          data-color="blue"
          data-placement="bottom"
          :title="data.title"
        >
          <span>{{ data.title }}</span>
        </button>
      </div>
    </router-link>
  </div>
</template>

<style scoped>
.tagbutton {
  padding: 0.375rem 0.75rem;
  background-color: black;
  font-weight: 600;
  font-size: 0.775rem;
  border: 0;
  max-width: calc(min(100vw/2.5, 180px));
  text-overflow: ellipsis;
  white-space: nowrap;
  overflow: hidden;
}
.tagbutton:hover {
  background-color: black !important;
  opacity: 80% !important;
}
</style>
