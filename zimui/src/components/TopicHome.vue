<script setup lang="ts">
import TopicSection from '../components/TopicSection.vue'
import TopicCard from '../components/TopicCard.vue'
import { onMounted, ref, watch, computed } from 'vue'
import Topic from '@/types/Topic'
import { useMainStore } from '../stores/main'
import TopicSectionType from '@/types/TopicSection'
import { transformTopicSectionOrSubSectionToCardData } from '@/types/TopicCardData'
import ToolBar from '../components/ToolBar.vue'
import { useLoading } from 'vue-loading-overlay'

const main = useMainStore()

const props = defineProps({
  slug: {
    type: String,
    default: undefined,
  },
})

const topic = ref<Topic>()
const dataLoaded = ref(false)
const $loading = useLoading()

const errMessage = computed(() => main.errorMessage)


/** Retrieve topic data */
const fetchData = async function () {
  const loader = $loading.show({
    loader: 'dots',
  })
  dataLoaded.value = false
  if (props.slug == undefined) {
    loader.hide()
    return
  }
  try {
    const resp = await main.fetchTopic(props.slug)
    if (resp) {
      topic.value = resp
    }
  } catch (error) {
    console.error('Error fetching topic:', error)
  }finally {
    loader.hide()
    dataLoaded.value = true
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
    topic.value.parents != undefined &&
    topic.value.parents.length > 0
  )
}

/** Navigate to the previous page */
const goToPreviousPage = () => {
  // click browser back button
  if (window.history.length > 1) {
    window.history.back()
  }
}
</script>

<template>
<div>
    <div v-if="errMessage" class="error-message" >
      Error: {{ errMessage }}
    </div>
  <div v-else>
  <div v-if="topic" class="content">
    <nav
      class="navbar navbar px-0 channel-navbar navbar-light fixed-top navbar-expand shadow"
    >
      <div class="justify-content-start mx-3 container-fluid">
        <ul aria-label="breadcrumb" class="navbar-nav">
          <ol class="bg-transparent breadcrumb flex-nowrap px-2 mt-3">
            <li
              v-if="topic.parents.length > ($grid.md ? 2 : 1)"
              class="active breadcrumb-item text-truncate"
              title="..."
            >
              ...
            </li>
            <li
              v-for="(parent, parentIndex) in topic.parents.slice(
                $grid.md ? -2 : -1,
              )"
              :key="parentIndex"
              :data="parent"
              class="breadcrumb-item text-truncate"
              :title="parent.title"
            >
              <router-link :to="`./${parent.slug}`">{{
                parent.title
              }}</router-link>
            </li>
            <li
              class="active breadcrumb-item text-truncate"
              :title="topic.title"
            >
              {{ topic.title }}
            </li>
          </ol>
        </ul>
      </div>
    </nav>
    <div
      v-if="dataLoaded"
      class="jumbotron"
      :class="{ 'with-description': topic.description }"
    >
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
            <button
              v-if="hasParents()"
              type="button"
              class="btn back-button rounded-circle btn-secondary light"
              @click="goToPreviousPage"
            >
              <FontAwesomeIcon
                aria-label="Arrow Left icon"
                icon="fa-solid fa-arrow-left"
              />
            </button>
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
    <div v-if="dataLoaded">
      <ToolBar
        v-if="getTopicSections(topic.sections).length > 0"
        :sections="getTopicSections(topic.sections)"
      />
      <TopicSection
        v-for="(content, contentIndex) in getTopicSections(topic.sections)"
        :key="contentIndex"
        :data="content"
      />
    </div>

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

.navbar {
  background-color: #12272a;
  height: 3.5rem;
  transition:
    color 0.15s ease-in-out,
    background-color 0.15s ease-in-out,
    border-color 0.15s ease-in-out,
    box-shadow 0.15s ease-in-out;
}

.breadcrumb-item a {
  text-decoration: underline;
  color: #a1a8a9;
}
.breadcrumb-item {
  color: #a1a8a9 !important;
}

.breadcrumb-item + .breadcrumb-item::before {
  float: left;
  padding-right: 0.5rem;
  color: #a1a8a9;
  content: '>';
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

.error-message {
  color: red;
  margin-top: 10px;
}

</style>
