<script setup lang="ts">
import { ref } from 'vue'
import { useMainStore } from '../stores/main'
import errimageData from '../assets/dead_kiwix.png'

const main = useMainStore()
const errimage = ref(errimageData)
</script>

<template>
  <div class="error-page">
    <div class="error-container">
      <div class="error-content">
        <p class="error-text">{{ main.errorMessage }}</p>
        <p class="error-text">{{ main.errorDetails }}</p>
      </div>
      <div class="error-image-container">
        <img :src="errimage" class="error-image" alt="error image" />
      </div>
    </div>
  </div>
</template>

<style scoped>

.error-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px;
  text-align: center;
}

.error-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 40px;
  margin: 60px 0;
  background: white;
  border-radius: 10px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  padding: 40px;
  flex-wrap: wrap;
}

.error-content {
  flex: 1;
  text-align: left;
}

.error-text {
  color: #222;
  margin: 10px 0;
  max-width: 500px;
  line-height: 1.6;
  font-size: 18px;
}

.error-image-container {
  flex: 1;
  display: flex;
  justify-content: center;
}

.error-image {
  max-width: 100%;
  height: auto;
}

@media (max-width: 768px) {
  .error-container {
    flex-direction: column;
    text-align: center;
  }
  
  .error-text {
    margin: 20px auto;
    font-size: 16px;
  }
  
  .error-image {
    width: 300px;
  }
}
</style>