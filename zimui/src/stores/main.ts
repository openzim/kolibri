import { defineStore } from 'pinia'
import axios, { AxiosError }from 'axios'
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

      return axios
        .get('./channel.json')
        .then((response) => {
          this.isLoading = false;
          this.channelData = response.data as Channel;
          return this.channelData; // Return the fetched channel data
        })
        .catch((error) => {
            this.isLoading = false
            this.channelData = null
          if (error instanceof AxiosError) {
            this.handleAxiosError(error);
          }
          else {
            this.errorMessage = 'Failed to load channel data';
          }
        });
    },
    async fetchTopic(slug: string) {
      this.isLoading = true
      this.errorMessage = ''
      return axios
        .get('./topics/' + slug + '.json')
        .then((response) => {
          this.isLoading = false;
          return response.data as Topic;
        })
        .catch((error) => {
            this.isLoading = false
            this.channelData = null
          if (error instanceof AxiosError) {
            this.handleAxiosError(error);
          }
          else {
            this.errorMessage = 'Failed to load node ' + slug + ' data';
          }
        });
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
          this.errorMessage = 'An Unexpected error occured';
        }
      }
    },
    setErrorMessage(message: string) {
      this.errorMessage = message
    },
  },
})
