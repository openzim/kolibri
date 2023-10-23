import TopicSection from './TopicSection'

/**
 * Data about current topic
 */
export default interface Topic {
  parentsSlugs: string[]
  title: string
  description: string
  sections: TopicSection[]
  thumbnail: string | null
}
