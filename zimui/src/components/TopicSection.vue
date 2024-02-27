<script setup lang="ts">
import { ref, getCurrentInstance } from 'vue'
import TopicCard from '../components/TopicCard.vue'
import TopicSubSection from '@/types/TopicSubSection'
import TopicCardData from '@/types/TopicCardData'
import { transformTopicSectionOrSubSectionToCardData } from '@/types/TopicCardData'

defineProps({
  data: {
    type: Object,
    required: true,
  },
})
const instance = getCurrentInstance()
const uid = ref('carroussel_' + instance?.uid)

/**
 * Keep only the 10 first items of the input array. If more than 10 items
 * were present in the list, a "magic/virtual" 11th item is created to indicate
 * that more items are available.
 * @param subsections - array of items to limit
 * @param sectionSlug - amount of items per chunk
 */
const limitCardsPerSections = (
  subsections: TopicSubSection[],
  sectionSlug: string,
): TopicCardData[] => {
  const maxCardPerSection = 10

  if (subsections.length > maxCardPerSection) {
    const slicedInput = subsections
      .slice(0, maxCardPerSection)
      .map(transformTopicSectionOrSubSectionToCardData)
    slicedInput.push({
      kind: 'more',
      count_more: subsections.length - maxCardPerSection,
      slug: sectionSlug,
    } as TopicCardData)
    return slicedInput
  }
  return subsections.map(transformTopicSectionOrSubSectionToCardData)
}

/**
 * Split an array of cards into chunks of cards. Each chunk is an array
 * of cards, with at most perChunk cards.
 * @param cards - array of cards to split into chunks
 * @param cardsPerChunk - amount of cards per chunk
 */
const splitCardsListIntoChunks = (
  cards: TopicCardData[],
  cardsPerChunk: number,
): TopicCardData[][] => {
  return cards.reduce(
    (
      cardsByChunks: TopicCardData[][],
      oneCard: TopicCardData,
      cardIndex: number,
    ) => {
      const chunkIndex = Math.floor(cardIndex / cardsPerChunk)
      cardsByChunks[chunkIndex] = (cardsByChunks[chunkIndex] || []).concat(
        oneCard,
      )
      return cardsByChunks
    },
    [],
  )
}

/**
 * Returns a class selector based on its name
 * @param className name of class
 */
const getClassSelector = (className: string): string => {
  return '#' + className
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
    <div :id="uid" class="carousel slide subsection-carousel-container" data-bs-wrap="false">
      <button
        v-if="data.subsections.length >= ($grid.lg ? 4 : $grid.sm ? 2 : 1)"
        class="carousel-control-prev"
        type="button"
        :data-bs-target="getClassSelector(uid)"
        data-bs-slide="prev"
      >
        <span style="color: black;" aria-hidden="true">
          <font-awesome-icon :icon="['fas', 'arrow-left']" />
        </span>
        <span class="visually-hidden">Previous</span>
      </button>
      <div class="container">
        <div 
          class="carousel-inner"
          :style="{
            minWidth:($grid.xxl ? '1168px' : ($grid.xl ? '988px' : ($grid.lg ? '808px' : ($grid.md ? '568px' : '')))),
            overflow: 'hidden',
          }"
        >
          <div
            v-for="(chunk, chunkIndex) in splitCardsListIntoChunks(
              limitCardsPerSections(data.subsections, data.slug),
              $grid.lg ? 4 : $grid.sm ? 2 : 1,
            )"
            :key="chunkIndex"
            class="carousel-item"
            :class="{ active: chunkIndex === 0 }"
            style="padding: 0px 10px;"
          >
            <div>
              <div class="row">
                <div
                  v-for="(item, itemIndex) in chunk"
                  :key="chunkIndex + '-' + itemIndex"
                  class="col-sm-6 col-md-6 col-lg-3"
                  :style="{ minWidth: $grid.xxl ? '270px' : $grid.xl ? '225px' : $grid.lg ? '180px' : $grid.md ? '267px' : $grid.sm ? '177px' : '100%'}"
                >
                  <TopicCard :data="item" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <button
        v-if="data.subsections.length >= ($grid.lg ? 4 : $grid.sm ? 2 : 1)"
        class="carousel-control-next"
        type="button"
        :data-bs-target="getClassSelector(uid)"
        data-bs-slide="next"
      >
        <span style="color: black;" aria-hidden="true">
          <font-awesome-icon :icon="['fas', 'arrow-right']" />
        </span>
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

.subsection-carousel-container {
	display: flex;
	justify-content: center;
	width: fit-content;
	margin: 0 auto;
}
</style>
