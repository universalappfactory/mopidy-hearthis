import logging
import traceback
from typing import List

from mopidy import backend, models

from .hearthis_search import HearThisLibrary

logger = logging.getLogger(__name__)


class HearthisLibraryProvider(backend.LibraryProvider):
    """Library for searching via hearthis.at api"""

    ROOT_DIRECTORY_URI = "hearthis:root"
    root_directory = models.Ref.directory(
        uri=ROOT_DIRECTORY_URI, name="Hearthis music community"
    )

    def __init__(self, backend, config):
        super().__init__(backend)

        username = config["hearthis"]["username"]
        password = config["hearthis"]["password"]
        self._hearthis_search = HearThisLibrary(username, password)

    def browse(self, uri) -> List[models.Ref]:
        try:
            if uri == "hearthis:root":
                return self._hearthis_search.browse()

            if uri.startswith("hearthis:feed"):
                return self._hearthis_search.get_feed_paged(uri)

            if uri.startswith("hearthis:news"):
                return self._hearthis_search.get_news(uri)

            if str(uri).startswith("hearthis:categories"):
                return self._hearthis_search.get_categories(str(uri))

            return []

        except Exception as e:
            traceback.print_exc()
            logger.exception(e)
            return []

    def lookup(self, uri):
        try:
            if uri.startswith("hearthis:album"):
                return self._hearthis_search.get_album_tracks(str(uri))
            if uri.startswith("hearthis:artist"):
                # return list(schema.lookup(self._connect(), Ref.ARTIST, uri))
                return self._hearthis_search.get_artist_tracks(str(uri))
            if uri.startswith("hearthis:track"):
                return self._hearthis_search.lookup_track(uri)
            if uri.startswith("hearthis:categories"):
                return self._hearthis_search.lookup_categories(str(uri))

            raise ValueError("Invalid lookup URI")
        except Exception as e:
            traceback.print_exc()
            logger.exception(e)
            return []

    def search(self, query=None, uris=None, exact=False):
        if "any" in query:
            any_query = query["any"]
            return self._hearthis_search.search(str(any_query[0]))

        if "album" in query:
            album_query = query["album"]
            return self._hearthis_search.search(str(album_query[0]))

        if "artist" in query:
            artist_query = query["artist"]
            return self._hearthis_search.search(str(artist_query[0]))

        return None
