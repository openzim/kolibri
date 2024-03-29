<script setup lang="ts">
import { PropType, ref } from 'vue'
import TopicCardData from '@/types/TopicCardData'
import imageData from '../assets/card_default_bg.png'

const image = ref(imageData)

defineProps({
  data: {
    type: Object as PropType<TopicCardData>,
    required: true,
  },
})
</script>

<template>
  <div v-if="data.kind == 'more'" class="card more">
    <router-link class="text-decoration-none text-reset" :to="`./${data.slug}`">
      <div class="card-body">
        <div class="card-content">
          <h5 class="card-title">More items ...</h5>
          <p class="card-text">
            There are {{ data.count_more }} more items in this section.
          </p>
        </div>
        <p class="card-text badge-wrapper">
          <span class="badge rounded-pill badge-primary">
            <FontAwesomeIcon icon="fa-regular fa-folder-open" />
            &nbsp;MORE
          </span>
        </p>
      </div>
    </router-link>
  </div>

  <div v-else-if="data.kind == 'topic'" class="card">
    <router-link class="text-decoration-none text-reset" :to="`./${data.slug}`">
      <img
        v-if="data.thumbnail"
        class="card-img-top"
        :src="`./thumbnails/${data.thumbnail}`"
      />
      <img v-else class="card-img-top" :src="image" />
      <div class="card-body" :class="{ 'with-description': data.description }">
        <div class="card-content">
          <h5 class="card-title">
            <span :title="data.title">{{ data.title }}</span>
          </h5>
          <span
            v-if="data.description"
            class="card-text"
            :title="data.description"
          >
            {{ data.description }}
          </span>
        </div>
        <p class="card-text badge-wrapper">
          <span class="badge rounded-pill badge-primary">
            <FontAwesomeIcon icon="fa-regular fa-folder-open" />
            &nbsp;EXPLORE
          </span>
        </p>
      </div>
    </router-link>
  </div>

  <div v-else class="card">
    <a class="text-decoration-none text-reset" :href="`./files/${data.slug}`">
      <img
        v-if="data.thumbnail"
        class="card-img-top"
        :src="`./thumbnails/${data.thumbnail}`"
      />
      <img v-else class="card-img-top" :src="image" />
      <div class="card-body" :class="{ 'with-description': data.description }">
        <div class="card-content">
          <h5 class="card-title">
            <span :title="data.title">{{ data.title }}</span>
          </h5>
          <span
            v-if="data.description"
            class="card-text"
            :title="data.description"
          >
            {{ data.description }}
          </span>
        </div>
        <p class="card-text badge-wrapper">
          <span class="badge rounded-pill badge-primary">
            <FontAwesomeIcon icon="fa-regular fa-file-lines" />
            &nbsp;OPEN
          </span>
        </p>
      </div>
    </a>
  </div>
</template>

<style scoped>
.card {
  background-color: #091415;
  border-radius: 1rem;
  color: white;
  height: 100%;
  overflow: hidden;
  top: 50%;
  transform: translateY(-50%);
}

.card-body{
  padding: 15px 15px 30px 15px;
}

.card-img-top {
  border-radius: 1rem 1rem 0 0;
  width: 100%; 
}

.badge {
  line-height: 20px;
}

.badge-primary {
  border-color: white;
  border-width: thin;
  border-style: solid;
}

.badge-wrapper {
  position: absolute;
  bottom: 15px; 
  left: 10px;
}

.more .card-content {
  height: calc(6rem - 2px);
}

.with-description .card-content {
  height: calc(9rem - 2px);
  flex: 1 1 auto;
}

.card-content {
  height: calc(3rem - 2px);
}

.card-text {
  display: -webkit-box;
  overflow: hidden;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}

.card-text a {
  text-decoration: none;
  color: white;
}

.card-title {
  display: -webkit-box;
  overflow: hidden;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
}

.text-decoration-none{
  display: flex;
  flex-direction: column;
  height: 100%;
}
</style>
