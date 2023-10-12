<script setup lang="ts">
import TopicSection from '../components/TopicSection.vue'
import TopicCard from '../components/TopicCard.vue'
import { onMounted, ref, watch } from 'vue'

import { useMainStore } from '../stores/main'
const main = useMainStore()

const props = defineProps({
  slug: {
    type: String,
    default: undefined,
  },
})

const data = ref()

const fetchData = async function () {
  if (props.slug == undefined) {
    return
  }
  data.value = await main.fetchTopic(props.slug)
  document.title = data.value.title
}

watch(props, fetchData)

onMounted(() => {
  fetchData()
})

const getTopicSections = (inputArray: any[]) => {
  return inputArray.filter((section) => section.kind == 'topic')
}

const getNonTopicSections = (inputArray: any[]) => {
  return inputArray.filter((section) => section.kind != 'topic')
}

const hasTopicAndNonTopicSection = (inputArray: any[]) => {
  return (
    getTopicSections(inputArray).length > 0 &&
    getNonTopicSections(inputArray).length > 0
  )
}
</script>

<template>
  <div v-if="data" class="content">
    <div class="jumbotron" :class="{ 'with-description': data.description }">
      <div class="container">
        <div
          class="align-items-start d-flex justify-content-between mt-5"
        ></div>
        <div class="row">
          <div
            :class="{
              'col-sm-8': data.thumbnail,
              'col-sm-12': !data.thumbnail,
            }"
          >
            <router-link :to="`./${data.parents[data.parents.length - 1]}`">
              <button
                v-if="data.parents.length > 0"
                type="button"
                class="btn back-button rounded-circle btn-secondary light"
              >
                <FontAwesomeIcon
                  aria-label="Arrow Left icon"
                  icon="fa-solid fa-arrow-left"
                />
              </button>
            </router-link>
            <h1 class="d-md-none h3">{{ data.title }}</h1>
            <h1 class="d-md-block d-none">{{ data.title }}</h1>
            <div class="lead mb-2">
              <span class="description" :title="data.description">
                {{ data.description }}
              </span>
            </div>
          </div>
          <div v-if="data.thumbnail" class="thumbnail col-sm-4">
            <img :src="`./thumbnails/${data.thumbnail}`" />
          </div>
        </div>
      </div>
    </div>
    <TopicSection
      v-for="(content, contentIndex) in getTopicSections(data.sections)"
      :key="contentIndex"
      :data="content"
    />

    <div v-if="hasTopicAndNonTopicSection(data.sections)" class="container">
      <div class="row">
        <h4 class="mt-4">
          <span> In this section: </span>
        </h4>
      </div>
    </div>

    <div class="container">
      <div class="row">
        <div
          v-for="(content, contentIndex) in getNonTopicSections(data.sections)"
          :key="contentIndex"
          class="col-sm-6 col-md-6 col-lg-3 pt-3 pb-3"
        >
          <TopicCard :data="content" />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.thumbnail img {
  max-width: 300px;
  max-height: 200px;
  display: flex;
  justify-content: flex-end;
}

.description {
  display: -webkit-box;
  overflow: hidden;
  -webkit-line-clamp: 6;
  -webkit-box-orient: vertical;
  overflow-wrap: break-word;
}

.jumbotron {
  background-color: #ece8e3;
  padding-top: 3.5rem;
  padding-bottom: 3.5rem;
}

.jumbotron.with-description {
  min-height: 349px;
}

.back-button {
  position: absolute;
  padding: 0;
  border: none;
  margin-left: calc(-46px - 1rem);
  width: 46px;
  height: 46px;
  background-color: rgba(18, 39, 42, 0.1);
  color: #12272a;
}
</style>
