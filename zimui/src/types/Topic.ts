import TopicSection from './TopicSection'
import TopicParent from './TopicParent'

/**
 * Data about current topic
 */
export default interface Topic {
  parents: TopicParent[]
  title: string
  description: string
  sections: TopicSection[]
  thumbnail: string | null
}
