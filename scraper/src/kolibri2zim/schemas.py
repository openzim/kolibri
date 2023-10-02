from pydantic import BaseModel


class TopicSubSection(BaseModel):
    slug: str
    title: str
    description: str
    kind: str
    thumbnail: str | None


class TopicSection(BaseModel):
    slug: str
    title: str
    description: str
    kind: str
    thumbnail: str | None
    subsections: list[TopicSubSection]


class Topic(BaseModel):
    parents: list[str]
    title: str
    description: str
    sections: list[TopicSection]
    thumbnail: str | None


class Channel(BaseModel):
    root: str
