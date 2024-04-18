import { defineStore } from 'pinia'
import axios, { AxiosError } from 'axios'
import Channel from '@/types/Channel'
import Topic from '@/types/Topic'

export type RootState = {
  channelData: Channel | null
  isLoading: boolean
  errorMessage: string
  errorDetails: string
}
export const useMainStore = defineStore('main', {
  state: () =>
    ({
      channelData: null,
      isLoading: false,
      errorMessage: '',
      errorDetails: '',
    }) as RootState,
  getters: {},
  actions: {
    async fetchChannel() {
      this.isLoading = true
      this.errorMessage = ''
      this.errorDetails = ''

      return axios.get('./channel.json').then(
        (response) => {
          this.isLoading = false
          this.channelData = response.data as Channel
        },
        (error) => {
          this.isLoading = false
          this.channelData = null
          this.errorMessage = 'Failed to load channel data.'
          if (error instanceof AxiosError) {
            this.handleAxiosError(error)
          }
        },
      )
    },
    async fetchTopic(slug: string) {
      this.isLoading = true
      this.errorMessage = ''
      return axios
        .get('./topics/' + slug + '.json')
        .then((response) => {
          this.isLoading = false
          return response.data as Topic
        })
        .catch((error) => {
          this.isLoading = false
          this.channelData = null
          this.errorMessage = 'Failed to load node ' + slug + ' data.'
          if (error instanceof AxiosError) {
            this.handleAxiosError(error)
          }
        })
    },
    handleAxiosError(error: AxiosError<object>) {
      if (axios.isAxiosError(error) && error.response) {
        const status = error.response.status
        switch (status) {
          case 400:
            this.errorDetails =
              'HTTP 400: Bad Request. The server could not understand the request.'
            break
          case 404:
            this.errorDetails =
              'HTTP 404: Not Found. The requested resource could not be found on the server.'
            break
          case 500:
            this.errorDetails =
              'HTTP 500: Internal Server Error. The server encountered an unexpected error.'
            break
        }
      }
    },
    setErrorMessage(message: string) {
      this.errorMessage = message
    },
  },
})
