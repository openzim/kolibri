import { defineStore } from 'pinia'
import axios, { AxiosError }from 'axios'
import Channel from '@/types/Channel'
import Topic from '@/types/Topic'

export type RootState = {
  channelData: Channel | null
  isLoading: boolean
  errorMessage: string
  error: AxiosError<object> | null
}
export const useMainStore = defineStore('main', {
  state: () =>
    ({
      channelData: null,
      isLoading: false,
      errorMessage: '',
      error: null,
    }) as RootState,
  getters: {},
  actions: {
    async fetchChannel() {
      this.isLoading = true
      this.errorMessage = ''
      try {
        const response = await axios.get('./channel.json')
        this.isLoading = false
        this.channelData = response.data as Channel
      } catch (error) {
        if (error instanceof AxiosError) {
          this.isLoading = false
          this.channelData = null
          this.handleAxiosError(error);
          if (!axios.isAxiosError(error)) {
            this.errorMessage = 'Failed to load channel data';
          }
          this.error = error // Set axios error to store
        }
      }
    },
    async fetchTopic(slug: string) {
      this.isLoading = true
      this.errorMessage = ''
      try {
        const response = await axios.get('./topics/' + slug + '.json')
        this.isLoading = false
        return response.data as Topic
      } catch (error: unknown) {
        if (error instanceof AxiosError) {
          this.isLoading = false
          this.channelData = null
          this.handleAxiosError(error);
          if (!axios.isAxiosError(error)) {
            this.errorMessage = 'Failed to load node ' + slug + ' data';
          }
          this.error = error // Set axios error to store
          return null
        }
      }
    },
    handleAxiosError(error: AxiosError<object>) {
      this.isLoading = false;
      this.channelData = null;
      if (axios.isAxiosError(error)) {
        if (error.response) {
          const status = error.response.status;
          switch (status) {
            case 400:
              this.errorMessage = 'Bad Request: The server could not understand the request due to invalid syntax.';
              break;
            case 401:
              this.errorMessage = 'Unauthorized: Authentication is required and has failed or has not yet been provided.';
              break;
            case 403:
              this.errorMessage = 'Forbidden: The server understood the request but refuses to authorize it.';
              break;
            case 404:
              this.errorMessage = 'Not Found: The requested resource could not be found on the server.';
              break;
            case 500:
              this.errorMessage = 'Internal Server Error: The server encountered an unexpected condition that prevented it from fulfilling the request.';
              break;
            default:
              this.errorMessage = 'An error occurred: ' + error.message;
              break;
          }
        } else {
          this.errorMessage = 'Network Error: Unable to connect to the server.';
        }
        this.error = error;
      }
    },
  },
})
