import TopicSection from './TopicSection'
import TopicSubSection from './TopicSubSection'

/**
 * Data about one card (either on topic subsection or a "more items" special card)
 */
export default interface TopicCardData {
  slug: string
  title: string
  description: string
  kind: string
  thumbnail: string | null
  count_more: number
}

export function transformTopicSectionOrSubSectionToCardData(
  value: TopicSection | TopicSubSection,
): TopicCardData {
  return {
    slug: value.slug,
    title: value.title,
    description: value.description,
    kind: value.kind,
    thumbnail: value.thumbnail,
  } as TopicCardData
}
