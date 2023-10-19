from humps import camelize
from pydantic import BaseModel


class CamelModel(BaseModel):
    """Model than transform Python snake_case into JSON camelCase"""

    class Config:
        alias_generator = camelize
        populate_by_name = True


class TopicSubSection(CamelModel):
    """One subclass to serialize data about one Kolibri topic"""

    slug: str
    title: str
    description: str
    kind: str
    thumbnail: str | None


class TopicSection(CamelModel):
    """Another subclass to serialize data about one Kolibri topic"""

    slug: str
    title: str
    description: str
    kind: str
    thumbnail: str | None
    subsections: list[TopicSubSection]


class Topic(CamelModel):
    """Class to serialize data about one Kolibri topic

    One topic is composed of parents, sections and subsections.
    This is already preprocessed information, closely adapted
    to current UI needs
    """

    parents_slugs: list[str]
    title: str
    description: str
    sections: list[TopicSection]
    thumbnail: str | None


class Channel(CamelModel):
    """Class to serialize data about the Kolibri channel"""

    root_slug: str
