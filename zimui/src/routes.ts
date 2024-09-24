import HomePage from './pages/HomePage.vue'

export const routes = [
  { path: '/', component: HomePage },
  { path: '/:topic', component: HomePage },
]
