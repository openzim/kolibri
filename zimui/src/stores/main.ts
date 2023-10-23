import { defineStore } from 'pinia'
import axios from 'axios'
import Channel from '@/types/Channel'
import Topic from '@/types/Topic'

export type RootState = {
  channelData: Channel | null
  isLoading: boolean
  errorMessage: string
}
export const useMainStore = defineStore('main', {
  state: () =>
    ({
      channelData: null,
      isLoading: false,
      errorMessage: '',
    }) as RootState,
  getters: {},
  actions: {
    async fetchChannel() {
      this.isLoading = true
      this.errorMessage = ''
      return axios.get('./channel.json').then(
        (response) => {
          this.isLoading = false
          this.channelData = response.data as Channel
        },
        (_) => {
          this.isLoading = false
          this.channelData = null
          this.errorMessage = 'Failed to load channel data'
        },
      )
    },
    async fetchTopic(slug: string) {
      this.isLoading = true
      this.errorMessage = ''
      return axios.get('./topics/' + slug + '.json').then(
        (response) => {
          this.isLoading = false
          return response.data as Topic
        },
        (_) => {
          this.isLoading = false
          this.channelData = null
          this.errorMessage = 'Failed to load node ' + slug + ' data'
          return null
        },
      )
    },
  },
})
