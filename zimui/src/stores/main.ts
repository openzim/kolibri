import { defineStore } from 'pinia'
import axios from 'axios'
export const useMainStore = defineStore('main', {
  state: () => ({
    channel_data: null,
    is_loading: false,
    error: '',
  }),
  getters: {},
  actions: {
    async fetchChannel() {
      this.is_loading = true
      this.error = ''
      try {
        const data = await axios.get('./channel.json')
        this.channel_data = data.data
      } catch (error) {
        this.error = 'Failed to load channel data'
        this.channel_data = null
        return false
      }
      this.is_loading = false
      return true
    },
    async fetchTopic(slug: string) {
      this.is_loading = true
      this.error = ''
      try {
        const data = await axios.get('./topics/' + slug + '.json')
        this.is_loading = false
        return data.data
      } catch (error) {
        this.error = 'Failed to load node ' + slug + ' data'
        this.is_loading = false
        return null
      }
    },
  },
})
