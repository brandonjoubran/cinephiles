import xml.etree.ElementTree as ET

from infrastructure.letterboxd_rss import _parse_feed, _parse_item

SAMPLE_ITEM = """
<item>
  <title>Test User watched One Hour Photo</title>
  <link>https://letterboxd.com/testuser/film/one-hour-photo/</link>
  <description><p>Great film.</p></description>
  <watchedDate>2025-03-10</watchedDate>
  <filmTitle>One Hour Photo</filmTitle>
  <filmYear>2002</filmYear>
  <memberRating>4.5</memberRating>
</item>
"""

SAMPLE_FEED = f"""<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    {SAMPLE_ITEM}
  </channel>
</rss>
"""


def test_parse_item_extracts_slug_and_watched_date():
    item = ET.fromstring(SAMPLE_ITEM)
    film = _parse_item(item)
    assert film is not None
    assert film.slug == "one-hour-photo"
    assert film.watched_date == "2025-03-10"
    assert film.rating == 4.5
    assert film.has_review is True


def test_parse_feed_returns_films():
    films = _parse_feed(SAMPLE_FEED)
    assert len(films) == 1
    assert films[0].slug == "one-hour-photo"
