/**
 * Data about current topic subsection (as returned by the API)
 */
export default interface TopicSubSection {
  slug: string
  title: string
  description: string
  kind: string
  thumbnail: string | null
}
