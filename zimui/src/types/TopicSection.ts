import TopicSubSection from './TopicSubSection'

/**
 * Data about current topic section
 */
export default interface TopicSection {
  slug: string
  title: string
  description: string
  kind: string
  thumbnail: string | null
  subsections: TopicSubSection[]
}
