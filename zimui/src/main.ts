import { createApp } from 'vue'
import { createRouter, createWebHashHistory } from 'vue-router'
import App from './App.vue'
import { routes } from './routes'
import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap'
import { library } from '@fortawesome/fontawesome-svg-core'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { faFolderOpen, faFileLines } from '@fortawesome/free-regular-svg-icons'
import { faArrowLeft, faArrowRight } from '@fortawesome/free-solid-svg-icons'
import './style.css'
import VueScreen from 'vue-screen'
import { createPinia } from 'pinia'

library.add(faFolderOpen, faArrowLeft, faArrowRight, faFileLines)

const app = createApp(App)

app.component('FontAwesomeIcon', FontAwesomeIcon)

app.use(VueScreen, 'bootstrap5')

const router = createRouter({
  history: createWebHashHistory(),
  routes: routes,
  scrollBehavior() {
    return { top: 0, behavior: 'smooth' }
  },
})

app.use(router)

const pinia = createPinia()
app.use(pinia)

app.mount('#app')
