<script setup lang="ts">
import { ref, getCurrentInstance } from 'vue'
import TopicCard from '../components/TopicCard.vue'

defineProps({
  data: {
    type: Object,
    required: true,
  },
})
const instance = getCurrentInstance()
const uid = ref('carroussel_' + instance?.uid)

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const splitChunks = (inputArray: any[], perChunk: number) => {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return inputArray.reduce((all: any[], one: ConcatArray<never>, i: number) => {
    const ch = Math.floor(i / perChunk)
    all[ch] = [].concat(all[ch] || [], one)
    return all
  }, [])
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const limitCardsPerSections = (inputArray: any[], section_slug: string) => {
  const maxCardPerSection = 10
  if (inputArray.length > maxCardPerSection) {
    const inputSliced = inputArray.slice(0, maxCardPerSection)
    inputSliced.push({
      kind: 'more',
      count_more: inputArray.length - maxCardPerSection,
      slug: section_slug,
    })
    return inputSliced
  }
  return inputArray
}

const getSelector = (value: string) => {
  return '#' + value
}
</script>

<template>
  <div class="subsection pt-3 pb-3">
    <div class="container pt-3">
      <router-link
        class="text-decoration-none text-reset"
        :to="`./${data.slug}`"
      >
        <h4 :class="{ 'mb-2': data.description, 'mb-4': !data.description }">
          <span>
            {{ data.title }}
            <span class="right-arrow">
              <FontAwesomeIcon
                aria-label="Arrow Right icon"
                icon="fa-solid fa-arrow-right"
              />
            </span>
          </span>
        </h4>
        <div v-if="data.description" class="lead mb-2">
          <span class="description" :title="data.description">
            {{ data.description }}
          </span>
        </div>
      </router-link>
    </div>
    <div :id="uid" class="carousel slide">
      <button
        class="carousel-control-prev"
        type="button"
        :data-bs-target="getSelector(uid)"
        data-bs-slide="prev"
      >
        <span class="carousel-control-prev-icon" aria-hidden="true"></span>
        <span class="visually-hidden">Previous</span>
      </button>
      <div class="carousel-inner">
        <div
          v-for="(chunk, chunkIndex) in splitChunks(
            limitCardsPerSections(data.subsections, data.slug),
            $grid.lg ? 4 : $grid.sm ? 2 : 1,
          )"
          :key="chunkIndex"
          class="carousel-item"
          :class="{ active: chunkIndex === 0 }"
        >
          <div class="container">
            <div class="row">
              <div
                v-for="(item, itemIndex) in chunk"
                :key="chunkIndex + '-' + itemIndex"
                class="col-sm-6 col-md-6 col-lg-3"
              >
                <TopicCard :data="item" />
              </div>
            </div>
          </div>
        </div>
      </div>
      <button
        class="carousel-control-next"
        type="button"
        :data-bs-target="getSelector(uid)"
        data-bs-slide="next"
      >
        <span class="carousel-control-next-icon" aria-hidden="true"></span>
        <span class="visually-hidden">Next</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.right-arrow {
  top: 0.1rem;
  left: 0.2rem;
  position: relative;
}

.carousel-control-next {
  width: 50px;
}

.carousel-control-prev {
  width: 50px;
}

.carousel-control-prev-icon {
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16' fill='%23000'%3e%3cpath d='M11.354 1.646a.5.5 0 0 1 0 .708L5.707 8l5.647 5.646a.5.5 0 0 1-.708.708l-6-6a.5.5 0 0 1 0-.708l6-6a.5.5 0 0 1 .708 0z'/%3e%3c/svg%3e");
}

.carousel-control-next-icon {
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16' fill='%23000'%3e%3cpath d='M4.646 1.646a.5.5 0 0 1 .708 0l6 6a.5.5 0 0 1 0 .708l-6 6a.5.5 0 0 1-.708-.708L10.293 8 4.646 2.354a.5.5 0 0 1 0-.708z'/%3e%3c/svg%3e");
}
</style>
