from pydantic import BaseModel


class TopicSubSection(BaseModel):
    """One subclass to serialize data about one Kolibri topic"""

    slug: str
    title: str
    description: str
    kind: str
    thumbnail: str | None


class TopicSection(BaseModel):
    """Another subclass to serialize data about one Kolibri topic"""

    slug: str
    title: str
    description: str
    kind: str
    thumbnail: str | None
    subsections: list[TopicSubSection]


class Topic(BaseModel):
    """Class to serialize data about one Kolibri topic

    One topic is composed of parents, sections and subsections.
    This is already preprocessed information, closely adapted
    to current UI needs
    """

    parents: list[str]
    title: str
    description: str
    sections: list[TopicSection]
    thumbnail: str | None


class Channel(BaseModel):
    """Class to serialize data about the Kolibri channel"""

    root: str
