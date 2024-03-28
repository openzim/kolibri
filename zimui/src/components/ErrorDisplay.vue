<script setup lang="ts">
import { ref } from 'vue';
import { useMainStore } from '../stores/main';
import errimageData from '../assets/Error.jpg'

const main = useMainStore()
const errimage = ref(errimageData)
</script>

<template>
  <div class="error-container">
    <img :src="errimage" class="error-image" />
    <p class="error-text">{{ main.errorMessage }}</p>
  </div>
</template>

<style scoped>
.error-container {
  text-align: center;
  padding: 20px;
}

.error-image {
  width: 300px;
  margin-bottom: 20px; 
}

.error-text {
  color: black;
  font-size: 16px;
}
</style>
