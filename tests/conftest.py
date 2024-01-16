from collections.abc import Callable, Generator
from typing import Any

import pytest

from kolibri2zim.scraper import Kolibri2Zim, KolibriDB
from kolibri2zim.scraper import options as expected_options_keys


class FakeDb(KolibriDB):
    def __init__(
        self,
        channel_name: str,
        channel_description: str,
        channel_author: str | None,
    ):
        self.channel_name = channel_name
        self.channel_description = channel_description
        self.channel_author = channel_author

    def get_channel_metadata(self, _):
        return {
            "name": self.channel_name,
            "description": self.channel_description,
            "author": self.channel_author,
        }


@pytest.fixture()
def channel_name() -> Generator[str, None, None]:
    yield "channel name"


@pytest.fixture()
def channel_description() -> Generator[str, None, None]:
    yield "channel description"


@pytest.fixture()
def channel_author() -> Generator[str, None, None]:
    yield "channel author"


@pytest.fixture()
def zim_name() -> Generator[str, None, None]:
    yield "a_name"


@pytest.fixture()
def scraper_generator(
    channel_name, channel_description
) -> Generator[Callable[..., Kolibri2Zim], None, None]:
    def _scraper(
        channel_name: str = channel_name,
        channel_description: str = channel_description,
        channel_author: str | None = None,
        additional_options: dict[str, Any] | None = None,
    ) -> Kolibri2Zim:
        options = {}
        for option_key in expected_options_keys:
            options[option_key] = None
        if additional_options:
            options.update(additional_options)
        scraper = Kolibri2Zim(**options)
        scraper.db = FakeDb(
            channel_author=channel_author,
            channel_description=channel_description,
            channel_name=channel_name,
        )
        return scraper

    yield _scraper
