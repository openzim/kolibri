import random
import re
import string
from collections.abc import Callable

import pytest
from conftest import FakeDb
from zimscraperlib.constants import MAXIMUM_DESCRIPTION_METADATA_LENGTH as MAX_DESC_LEN
from zimscraperlib.constants import (
    MAXIMUM_LONG_DESCRIPTION_METADATA_LENGTH as MAX_LONG_DESC_LEN,
)

from kolibri2zim.entrypoint import parse_args
from kolibri2zim.scraper import Kolibri2Zim


def randomword(length):
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for i in range(length))  # noqa: S311


def test_sanitize_defaults_ok(scraper_generator: Callable[..., Kolibri2Zim]):
    scraper = scraper_generator()
    scraper.sanitize_inputs()


TEXT_NOT_USED = "text not used"

LONG_TEXT = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor "
    "incididunt ut labore et dolore magna aliqua. At erat pellentesque adipiscing "
    "commodo elit at imperdiet. Rutrum tellus pellentesque eu tincidunt tortor aliquam"
    " nulla facilisi. Eget lorem dolor sed viverra ipsum nunc. Ipsum nunc aliquet "
    "bibendum enim facilisis gravida neque convallis. Aliquam malesuada bibendum arcu "
    "vitae elementum curabitur. Platea dictumst quisque sagittis purus sit amet "
    "volutpat. Blandit libero volutpat sed cras ornare. In eu mi bibendum neque "
    "egestas. Egestas dui id ornare arcu odio. Pulvinar neque laoreet suspendisse "
    "interdum. Fames ac turpis egestas integer eget aliquet nibh praesent tristique. Et"
    " egestas quis ipsum suspendisse ultrices gravida dictum fusce. Malesuada fames ac "
    "turpis egestas. Tincidunt nunc pulvinar sapien et ligula ullamcorper malesuada "
    "proin libero. In arcu cursus euismod quis viverra. Faucibus in ornare quam viverra"
    ". Curabitur vitae nunc sed velit dignissim sodales ut eu sem. Velit scelerisque in"
    " dictum non consectetur a erat nam. Proin fermentum leo vel orci porta non. Fames"
    " ac turpis egestas sed tempus. Vitae justo eget magna fermentum iaculis eu non. "
    "Imperdiet massa tincidunt nunc pulvinar sapien et ligula. Laoreet sit amet cursus "
    "sit amet dictum sit amet. Quis hendrerit dolor magna eget. Orci ac auctor augue "
    "mauris augue. Consequat interdum varius sit amet mattis. At ultrices mi tempus "
    "imperdiet nulla malesuada pellentesque elit. Volutpat est velit egestas dui. "
    "Potenti nullam ac tortor vitae. At tempor commodo ullamcorper a lacus vestibulum "
    "sed arcu non. Duis ut diam quam nulla. Vestibulum mattis ullamcorper velit sed "
    "ullamcorper. Sit amet commodo nulla facilisi nullam vehicula. Faucibus purus in "
    "massa tempor nec feugiat. Sem fringilla ut morbi tincidunt augue interdum velit. "
    "Etiam dignissim diam quis enim lobortis scelerisque fermentum dui. Nunc vel risus "
    "commodo viverra maecenas accumsan. Aenean sed adipiscing diam donec adipiscing "
    "tristique. Maecenas accumsan lacus vel facilisis volutpat est velit egestas. Nulla"
    " aliquet porttitor lacus luctus accumsan tortor posuere ac. Habitant morbi "
    "tristique senectus et netus et. Eget mi proin sed libero enim sed faucibus turpis "
    "in. Vulputate enim nulla aliquet porttitor lacus. Dui ut ornare lectus sit amet "
    "est. Quam lacus suspendisse faucibus interdum posuere. Sagittis orci a scelerisque"
    " purus semper eget duis at tellus. Tellus molestie nunc non blandit massa. Feugiat"
    " vivamus at augue eget arcu dictum varius duis at. Varius morbi enim nunc faucibus"
    " a pellentesque sit. Id aliquet lectus proin nibh nisl condimentum id venenatis a."
    " Tortor dignissim convallis aenean et tortor at risus viverra adipiscing. Aliquam "
    "malesuada bibendum arcu vitae elementum curabitur vitae nunc sed. Habitasse platea"
    " dictumst quisque sagittis purus sit amet volutpat. Vitae auctor eu augue ut "
    "lectus. At varius vel pharetra vel turpis nunc eget. Dictum at tempor  commodo "
    "ullamcorper a lacus vestibulum sed arcu. Pellentesque massa placerat duis "
    "ultricies. Enim nunc faucibus a pellentesque sit amet porttitor eget dolor. "
    "Volutpat blandit aliquam etiam erat velit scelerisque in. Amet mattis vulputate "
    "enim nulla aliquet porttitor. Egestas maecenas pharetra convallis posuere morbi "
    "leo urna molestie. Duis ut diam quam nulla porttitor massa id. In fermentum "
    "posuere urna nec tincidunt praesent. Turpis egestas sed tempus urna et pharetra "
    "pharetra massa. Tellus molestie nunc non blandit massa. Diam phasellus vestibulum "
    "lorem sed risus ultricies. Egestas erat imperdiet sed euismod nisi porta lorem. "
    "Quam viverra orci sagittis eu volutpat odio facilisis mauris sit. Ornare aenean "
    "euismod elementum nisi quis. Laoreet non curabitur gravida arcu ac tortor "
    "dignissim convallis aenean. Sagittis aliquam malesuada bibendum arcu vitae "
    "elementum. Sed blandit libero volutpat sed cras ornare. Sagittis eu volutpat odio "
    "facilisis mauris. Facilisis volutpat est velit egestas dui id ornare arcu odio. "
    "Eu feugiat pretium  nibh."
)


@pytest.mark.parametrize(
    "cli_description, cli_long_description, channel_description, raises, "
    "expected_description, expected_long_description",
    [
        # CLI description set and is short, CLI long descripion not set, channel
        # description doe not matter
        (
            LONG_TEXT[0:MAX_DESC_LEN],
            None,
            TEXT_NOT_USED,
            False,
            LONG_TEXT[0:MAX_DESC_LEN],
            None,
        ),
        # CLI description set and is too long, channel description does not matter
        (LONG_TEXT[0 : MAX_DESC_LEN + 1], None, TEXT_NOT_USED, True, None, None),
        # CLI description not set and channel description is short enough
        (None, None, LONG_TEXT[0:MAX_DESC_LEN], False, LONG_TEXT[0:MAX_DESC_LEN], None),
        # CLI description not set and channel description is too long for description
        # but ok for long description
        (
            None,
            None,
            LONG_TEXT[0 : MAX_DESC_LEN + 1],
            False,
            LONG_TEXT[0 : MAX_DESC_LEN - 1] + "…",
            LONG_TEXT[0 : MAX_DESC_LEN + 1],
        ),
        (
            None,
            None,
            LONG_TEXT[0:MAX_LONG_DESC_LEN],
            False,
            LONG_TEXT[0 : MAX_DESC_LEN - 1] + "…",
            LONG_TEXT[0:MAX_LONG_DESC_LEN],
        ),
        # CLI description not set and channel description is too long for description
        # and long description
        (
            None,
            None,
            LONG_TEXT[0 : MAX_LONG_DESC_LEN + 1],
            False,
            LONG_TEXT[0 : MAX_DESC_LEN - 1] + "…",
            LONG_TEXT[0 : MAX_LONG_DESC_LEN - 1] + "…",
        ),
        # CLI description set and is short, CLI long descripion set and is short,
        # channel description does not matter
        (
            LONG_TEXT[0:MAX_DESC_LEN],
            LONG_TEXT[0:MAX_LONG_DESC_LEN],
            TEXT_NOT_USED,
            False,
            LONG_TEXT[0:MAX_DESC_LEN],
            LONG_TEXT[0:MAX_LONG_DESC_LEN],
        ),
        # CLI description set and is short, CLI long descripion set and is too long,
        # channel description does not matter
        (
            LONG_TEXT[0:MAX_DESC_LEN],
            LONG_TEXT[0 : MAX_LONG_DESC_LEN + 1],
            TEXT_NOT_USED,
            True,
            None,
            None,
        ),
        # CLI description not set, CLI long descripion set and is short,
        # channel description set to something different than long desc
        (
            None,
            LONG_TEXT[0:MAX_LONG_DESC_LEN],
            LONG_TEXT[10:MAX_LONG_DESC_LEN],
            False,
            LONG_TEXT[10 : MAX_DESC_LEN + 9] + "…",
            LONG_TEXT[0:MAX_LONG_DESC_LEN],
        ),
    ],
)
def test_description(
    cli_description: str,
    cli_long_description: str,
    channel_description: str,
    *,
    raises: bool,
    expected_description: str,
    expected_long_description: str,
    scraper_generator: Callable[..., Kolibri2Zim],
):
    if channel_description:
        scraper = scraper_generator(
            channel_description=channel_description,
            additional_options={
                "description": cli_description,
                "long_description": cli_long_description,
            },
        )
    else:
        scraper = scraper_generator(
            additional_options={
                "description": cli_description,
                "long_description": cli_long_description,
            }
        )

    if raises:
        with pytest.raises(ValueError):
            scraper.sanitize_inputs()
        return
    else:
        scraper.sanitize_inputs()

    assert scraper.description == expected_description
    assert scraper.long_description == expected_long_description


def test_no_required_args():
    with pytest.raises(expected_exception=SystemExit):
        parse_args([])


def test_defaults_args(channel_name, channel_description, channel_author, zim_name):
    args = parse_args(["--name", zim_name])
    scraper = Kolibri2Zim(**dict(args._get_kwargs()))
    scraper.db = FakeDb(
        channel_name=channel_name,
        channel_description=channel_description,
        channel_author=channel_author,
    )
    scraper.sanitize_inputs()
    assert scraper.language == "eng"
    assert scraper.publisher == "openZIM"
    assert scraper.author == channel_author
    assert scraper.title == channel_name
    assert scraper.description == channel_description
    assert scraper.name == zim_name
    assert re.match(
        pattern=f"{zim_name}_\\d{{4}}-\\d{{2}}\\.zim", string=scraper.clean_fname
    )
    # We compare sets because ordering does not matter
    assert set(scraper.tags) == {"_category:other", "kolibri", "_videos:yes"}
    assert len(scraper.tags) == 3
