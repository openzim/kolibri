<script setup lang="ts">
defineProps({
  data: {
    type: Object,
    required: true,
  },
})
</script>

<template>
  <div v-if="data.kind == 'topic'">
    <router-link class="text-decoration-none text-reset" :to="`./${data.slug}`">
      <div role="group" class="mx-1 my-1 btn-group btn-group-sm">
        <a class="btn btn-primary btn-sm rounded-pill tagbutton">
          {{ data.title }}
        </a>
      </div>
    </router-link>
  </div>
  <div v-else>
    <div role="group" class="mx-1 my-1 btn-group btn-group-sm">
      <a
        class="btn btn-primary btn-sm rounded-pill tagbutton"
        :href="`./files/${data.slug}`"
      >
        {{ data.title }}
      </a>
    </div>
  </div>
</template>

<style scoped>
.tagbutton {
  padding: 0.375rem 0.75rem;
  background-color: black;
  font-weight: 600;
  font-size: 0.775rem;
  border: 0;
}
.tagbutton:hover {
  background-color: black !important;
  opacity: 80% !important;
}
</style>
