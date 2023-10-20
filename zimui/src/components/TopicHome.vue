<script setup lang="ts">
import TopicSection from '../components/TopicSection.vue'
import TopicCard from '../components/TopicCard.vue'
import { onMounted, ref, watch } from 'vue'
import Topic from '@/types/Topic'
import { useMainStore } from '../stores/main'
import TopicSectionType from '@/types/TopicSection'
import { transformTopicSectionOrSubSectionToCardData } from '@/types/TopicCardData'

const main = useMainStore()

const props = defineProps({
  slug: {
    type: String,
    default: undefined,
  },
})

const topic = ref<Topic>()

/** Retrieve topic data */
const fetchData = async function () {
  if (props.slug == undefined) {
    return
  }
  const resp = await main.fetchTopic(props.slug)
  if (resp) {
    topic.value = resp
  }
}

watch(props, fetchData)

onMounted(() => {
  fetchData()
})

/** Return sections whose kind is 'topic' */
const getTopicSections = (topics: TopicSectionType[]): TopicSectionType[] => {
  return topics.filter((section) => section.kind == 'topic')
}

/** Return sections whose kind is not 'topic' */
const getNonTopicSections = (
  topics: TopicSectionType[],
): TopicSectionType[] => {
  return topics.filter((section) => section.kind != 'topic')
}

/** Return true if section has a mix of topic and non-topic sectionss */
const hasTopicAndNonTopicSection = (topics: TopicSectionType[]): boolean => {
  return (
    getTopicSections(topics).length > 0 &&
    getNonTopicSections(topics).length > 0
  )
}

/** Return true if node has at least on parent */
const hasParents = (): boolean => {
  return (
    topic.value != undefined &&
    topic.value.parentsSlugs != undefined &&
    topic.value.parentsSlugs.length > 0
  )
}

/** Return the slug of the last parent in the parents hierarchy */
const parentSlug = (): string | null => {
  if (!topic.value || !topic.value.parentsSlugs) {
    return null
  }
  return topic.value.parentsSlugs[topic.value.parentsSlugs.length - 1]
}
</script>

<template>
  <div v-if="topic" class="content">
    <div class="jumbotron" :class="{ 'with-description': topic.description }">
      <div class="container">
        <div
          class="align-items-start d-flex justify-content-between mt-5"
        ></div>
        <div class="row">
          <div
            :class="{
              'col-sm-8': topic.thumbnail,
              'col-sm-12': !topic.thumbnail,
            }"
          >
            <router-link :to="`./${parentSlug()}`">
              <button
                v-if="hasParents()"
                type="button"
                class="btn back-button rounded-circle btn-secondary light"
              >
                <FontAwesomeIcon
                  aria-label="Arrow Left icon"
                  icon="fa-solid fa-arrow-left"
                />
              </button>
            </router-link>
            <h1 class="d-md-none h3">{{ topic.title }}</h1>
            <h1 class="d-md-block d-none">{{ topic.title }}</h1>
            <div class="lead mb-2">
              <span class="description" :title="topic.description">
                {{ topic.description }}
              </span>
            </div>
          </div>
          <div v-if="topic.thumbnail" class="thumbnail col-sm-4">
            <img :src="`./thumbnails/${topic.thumbnail}`" />
          </div>
        </div>
      </div>
    </div>
    <TopicSection
      v-for="(content, contentIndex) in getTopicSections(topic.sections)"
      :key="contentIndex"
      :data="content"
    />

    <div v-if="hasTopicAndNonTopicSection(topic.sections)" class="container">
      <div class="row">
        <h4 class="mt-4">
          <span> In this section: </span>
        </h4>
      </div>
    </div>

    <div class="container">
      <div class="row">
        <div
          v-for="(content, contentIndex) in getNonTopicSections(topic.sections)"
          :key="contentIndex"
          class="col-sm-6 col-md-6 col-lg-3 pt-3 pb-3"
        >
          <TopicCard
            :data="transformTopicSectionOrSubSectionToCardData(content)"
          />
        </div>
      </div>
      <div class="row">
        <footer class="pt-2 pb-3">
          <a href="./files/about">About this content</a>
        </footer>
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

footer {
  text-align: center;
}
</style>
