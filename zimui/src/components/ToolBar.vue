<script setup lang="ts">
import TopicSectionType from '@/types/TopicSection'
import { PropType, onMounted, ref, watch } from 'vue'
import TagButton from '../components/TagButton.vue'

const props = defineProps({
  sections: {
    type: Object as PropType<TopicSectionType[]>,
    required: true,
  },
})

const tags = ref<
  {
    title: string
    slug: string
  }[]
>()

const showMore = ref(false)

/**
 * Limit number of tags based on max number of characters toolbar container can accomodate
 * maxCharacters = toolbar container width / 7 :150 (dividing factor should be adjusted based on font-size)
 * Magic 150: With tag button max width (180px) and font size (0.775rem),
 * we fit max 25-27 characters per tag.
 * Thus, 150 characters allow for 6-7 tags if container width isn't accessible.
 * Magic 25: We display a maximum of ~25 characters per tag.
 * To maximize tag count, we deduct only 25 characters from charLeft,
 * as we typically utilize no more than 25 characters' worth of space.
 * @returns number of tags to display
 */
const lengthOfTags = function () {
  const containerWidth = document.querySelector('.container')?.clientWidth
  const totalCharacters = props.sections.reduce(
    (acc, content) => acc + content.title.length,
    0,
  )
  const maxCharacters = containerWidth ? containerWidth / 7 : 150

  let tagsToDisplay = props.sections.length
  if (totalCharacters > maxCharacters) {
    let charLeft = maxCharacters
    for (let i = 0; i < props.sections.length; i++) {
      charLeft -= Math.min(props.sections[i].title.length, 25)
      if (charLeft < 0) {
        tagsToDisplay = i + 1
        break
      }
    }
  }
  return tagsToDisplay
}

/** Retrieve limited number of tags */
const getMaxTags = function () {
  tags.value = props.sections.slice(0, lengthOfTags()).map((content) => {
    return {
      title: content.title,
      slug: content.slug,
    }
  })
}

/** Retrieve all or less tags*/
const showMoreOrLess = function () {
  if (showMore.value) {
    getMaxTags()
  } else {
    tags.value = props.sections.map((content) => ({
      title: content.title,
      slug: content.slug,
    }))
  }
  showMore.value = !showMore.value
}

watch(props, () => {
  showMore.value = false
  getMaxTags()
})

onMounted(() => {
  getMaxTags()
  window.addEventListener('resize', () => {
    showMore.value = false
    getMaxTags()
  })
})
</script>

<template>
  <div
    style="align-items: baseline"
    class="mt-2 container btn-toolbar toolbar"
    role="toolbar"
  >
    <TagButton v-for="content in tags" :key="content.slug" :data="content" />
    <div v-if="lengthOfTags() < sections.length">
      <button
        style="font-size: 0.7rem"
        class="btn mt-1 mx-1 py-0 btn-primary btn-sm rounded-pill tagbutton"
        @click="showMoreOrLess"
      >
        <span>
          {{ showMore ? 'Show less...' : 'Show more...' }}
        </span>
      </button>
    </div>
  </div>
</template>

<style scoped></style>
