import asyncio
import logging
import re
import traceback
from typing import List, NamedTuple, Tuple

import aiohttp
from mopidy import models
from pyhearthis.hearthis import FeedType, HearThis
from pyhearthis.models import Category, SingleTrack

logger = logging.getLogger(__name__)


class TrackNotFound(Exception):
    pass


class ArtistNotFound(Exception):
    pass


class TrackTuple(NamedTuple):
    uri: str
    ref_uri: str
    model_track: models.Track
    single_track: SingleTrack


class ArtistTuple(NamedTuple):
    uri: str
    permalink: str
    model_artist: models.Artist
    artist: models.Artist


class CategoryTuple(NamedTuple):
    category: Category
    ref: models.Ref


def create_artist_url(track_or_user_id) -> str:

    if isinstance(track_or_user_id, SingleTrack):
        return f"hearthis:artist:{track_or_user_id.user_id}"

    return f"hearthis:artist:{track_or_user_id}"


def create_track_url(track_or_track_id) -> str:

    if isinstance(track_or_track_id, SingleTrack):
        return f"hearthis:track:{track_or_track_id.id}"

    return f"hearthis:track:{track_or_track_id}"


def pad_zero(value):

    if isinstance(value, int):
        if value < 10:
            return f"0{value}"
        return f"{value}"

    if len(value) > 1:
        return f"0{value}"
    return value


def with_page_folders(
    items: List[models.Ref], prefix, current_page: int
) -> List[models.Ref]:
    items.insert(
        0,
        models.Ref.directory(
            uri=f"{prefix}:{current_page+1}",
            name=f"Page {pad_zero(current_page + 1)}",
        ),
    )

    if current_page > 1:
        prev_page = current_page - 1
        items.insert(
            0,
            models.Ref.directory(
                uri=f"{prefix}:{prev_page}", name=f"Page {pad_zero(prev_page)}"
            ),
        )

    return items


class HearThisLibrary:
    def __init__(self, username, password):
        self._username = username
        self._password = password
        self._user = None
        self._cache = ModelCache()
        self._page_count = 20

    def _get_user(self):
        if self._user is None:
            self._user = asyncio.run(self._login())
        return self._user

    async def _login(self):
        async with aiohttp.ClientSession() as session:
            hearthis = HearThis(session)
            return await hearthis.login(self._username, self._password)

    async def _search_async(self, user, query):
        async with aiohttp.ClientSession() as session:
            hearthis = HearThis(session)
            return await hearthis.search(user, query, None, None, 1, 20)

    async def _get_feed_async(self, user, feed_type: FeedType, page=1):
        async with aiohttp.ClientSession() as session:
            hearthis = HearThis(session)
            return await hearthis.get_feeds(
                user, feed_type=feed_type, page=page, count=self._page_count
            )

    async def _get_tracks_from_category_async(
        self, user, category: Category, page=1
    ):
        async with aiohttp.ClientSession() as session:
            hearthis = HearThis(session)
            return await hearthis.get_category_tracks(
                user, category, page, self._page_count
            )

    def _get_tracks_from_category(self, user, category: Category, page=1):
        return asyncio.run(
            self._get_tracks_from_category_async(user, category, page)
        )

    async def _get_categories_async(self):
        async with aiohttp.ClientSession() as session:
            hearthis = HearThis(session)
            return await hearthis.get_categories()

    def _get_categories(self) -> List[Category]:
        return asyncio.run(self._get_categories_async())

    async def _get_artist_tracks_async(self, user, artist_permalink: str):
        async with aiohttp.ClientSession() as session:
            hearthis = HearThis(session)
            return await hearthis.get_artist_tracks(user, artist_permalink)

    def _get_artist_tracks(self, user, artist_permalink: str):
        return asyncio.run(
            self._get_artist_tracks_async(user, artist_permalink)
        )

    def _track_as_ref(self, item: Tuple[ArtistTuple, TrackTuple]) -> models.Ref:
        track_tuple = self._cache.get_track(item[1].single_track.stream_url)
        if track_tuple is None:
            raise TrackNotFound()

        return models.Ref.track(
            uri=create_track_url(track_tuple.single_track),
            name=track_tuple.single_track.title,
        )

    def _as_ref(
        self, track_models: List[Tuple[ArtistTuple, TrackTuple]]
    ) -> List[models.Ref]:
        return list(map(self._track_as_ref, track_models))

    def _search(self, user, query) -> List[SingleTrack]:
        return asyncio.run(self._search_async(user, query))

    def _get_feed(self, user, feed_type: FeedType, page=1):
        return asyncio.run(self._get_feed_async(user, feed_type, page))

    def browse(self, parent=None) -> List[models.Ref]:
        result = []

        if parent is None:
            result.append(
                models.Ref.directory(uri="hearthis:feed", name="Feed")
            )

        if parent is None:
            result.append(
                models.Ref.directory(
                    uri="hearthis:categories", name="Categories"
                )
            )

        if parent is None:
            result.append(
                models.Ref.directory(uri="hearthis:news", name="News")
            )

        return result

    def get_categories(self, uri) -> List[models.Ref]:
        result = re.match(
            "hearthis:categories:(_[p]\\:)?(.[a-z]+)\\:?(\\d+)?.*", uri
        )

        user = self._get_user()
        if result and result.group(2):
            page = int(result.group(3)) if result.group(3) else 1
            category = self._cache.get_category(result.group(2))
            if category:
                if page:
                    tracks = self._get_tracks_from_category(
                        user, category, page
                    )
                else:
                    tracks = self._get_tracks_from_category(user, category)

                track_models = ModelFactory.create_track_models(tracks)
                self._cache.add_models(track_models)
                refs = self._as_ref(track_models)
                return with_page_folders(
                    refs, f"hearthis:categories:_p:{category.id}", page
                )

            return None
        else:
            categories = []
            if self._cache.has_categories():
                categories = self._cache.get_categories()
            else:
                categories = self._get_categories()
                self._cache.add_categories(categories)

            return ModelFactory.create_directory_refs(categories)

    def lookup_categories(self, uri) -> List[models.Track]:
        # ToDo
        logger.debug("TODO lookup_categories")
        return []

    def lookup_track(self, uri) -> List[models.Track]:
        logger.debug(f"lookup_track {uri}")
        track_tuple = self._cache.get_track_by_ref_url(uri)
        return [track_tuple.model_track]

    def get_feed(
        self, feed_type: FeedType = FeedType.UNDEFINED, page=1
    ) -> List[models.Ref]:
        user = self._get_user()
        tracks = self._get_feed(user, feed_type, page)
        track_models = ModelFactory.create_track_models(tracks)
        self._cache.add_models(track_models)
        return self._as_ref(track_models)

    def get_feed_paged(self, uri):
        page_result = re.match("hearthis\\:feed\\:(\\d+)?", uri)
        if page_result and page_result.group(1):
            return with_page_folders(
                self.get_feed(FeedType.UNDEFINED, int(page_result.group(1))),
                "hearthis:feed",
                int(page_result.group(1)),
            )
        return with_page_folders(self.get_feed(), "hearthis:feed", 1)

    def get_news(self, uri) -> List[models.Ref]:
        page_result = re.match("hearthis\\:news\\:(\\d+)?", uri)
        if page_result and page_result.group(1):
            return with_page_folders(
                self.get_feed(FeedType.NEW, int(page_result.group(1))),
                "hearthis:news",
                int(page_result.group(1)),
            )
        return with_page_folders(
            self.get_feed(FeedType.NEW), "hearthis:news", 1
        )

    def get_artist_tracks(self, uri):

        if not self._cache.artist_tracks_complete(uri):
            user = self._get_user()
            artist = self._cache.get_artist(uri)
            artist_tracks = self._get_artist_tracks(user, artist.permalink)
            models = ModelFactory.create_track_models(artist_tracks)
            self._cache.add_models(models, True)

        result = list(
            map(
                lambda t: t.model_track, self._cache.get_artist_tracks(str(uri))
            )
        )
        return result if result is not None else []

    def _create_search_result(
        self, url: str, items: List[Tuple[ArtistTuple, TrackTuple]]
    ):
        artist_list = []
        track_list = []
        album_list = []

        for item in items:
            artist_list.append(item[0].model_artist)
            track_list.append(item[1].model_track)

        return models.SearchResult(
            uri=url, albums=album_list, artists=artist_list, tracks=track_list
        )

    def search(self, query) -> models.SearchResult:
        try:
            user = self._get_user()
            tracks = self._search(user, query)

            models = ModelFactory.create_track_models(tracks)
            self._cache.add_models(models)
            url = f"hearthis://search/{query}"

            return self._create_search_result(url, models)
        except Exception as e:
            traceback.print_exc()
            logger.exception(e)

        return None


class ModelCache:
    def __init__(self) -> None:
        self._tracks_stream_url = {}
        self._tracks_ref_url = {}
        self._artist_tracks = {}
        self._artists = {}
        self._categories = {}

    def add_model(
        self,
        model: Tuple[ArtistTuple, TrackTuple],
        complete_artist_tracks: bool = False,
    ):
        if not model[1].single_track.stream_url in self._tracks_stream_url:
            self._tracks_stream_url[model[1].single_track.stream_url] = model

        ref_url = create_track_url(model[1].single_track)
        if ref_url not in self._tracks_ref_url:
            self._tracks_ref_url[ref_url] = model

        artist_url = create_artist_url(model[1].single_track)
        if artist_url not in self._artist_tracks:
            self._artist_tracks[artist_url] = (complete_artist_tracks, [model])
        else:
            tmp = self._artist_tracks[artist_url]
            self._artist_tracks[artist_url] = (
                complete_artist_tracks,
                [*tmp[1], model],
            )

        if artist_url not in self._artists:
            self._artists[artist_url] = model[0]

    def add_models(
        self,
        models: List[Tuple[ArtistTuple, TrackTuple]],
        complete_artist_tracks: bool = False,
    ) -> None:
        for model in models:
            self.add_model(model, complete_artist_tracks)

    def artist_tracks_complete(self, uri: str) -> bool:
        if uri in self._artist_tracks:
            artist_tuple = self._artist_tracks[uri]
            return artist_tuple[0]

        return False

    def get_artist_tracks(self, uri: str) -> List[TrackTuple]:
        if uri in self._artist_tracks:
            return list(map(lambda t: t[1], self._artist_tracks[uri][1]))

    def get_artist(self, uri: str) -> ArtistTuple:
        if uri in self._artists:
            return self._artists[uri]
        return None

    def get_categories(self) -> List[Category]:
        return self._categories.values()

    def get_category(self, category_id) -> Category:
        if category_id in self._categories:
            return self._categories[category_id]
        return None

    def has_categories(self) -> bool:
        return len(self._categories) > 0

    def add_category(self, category: Category) -> None:
        if category.id not in self._categories:
            self._categories[category.id] = category

    def add_categories(self, categories: List) -> None:
        for category in categories:
            self.add_category(category)

    def get_track_by_ref_url(self, ref_url) -> TrackTuple:
        if ref_url in self._tracks_ref_url:
            return self._tracks_ref_url[ref_url][1]
        return None

    def get_track(self, stream_url: str) -> TrackTuple:
        if stream_url in self._tracks_stream_url:
            return self._tracks_stream_url[stream_url][1]
        return None


class ModelFactory:
    @staticmethod
    def _create_track(track: SingleTrack) -> Tuple[ArtistTuple, TrackTuple]:
        artist_url = create_artist_url(track)
        artist_name = track.user.username
        artist_tuple = ArtistTuple(
            artist_url,
            None,
            models.Artist(uri=artist_url, name=artist_name),
            None,
        )
        track_tuple = TrackTuple(
            track.stream_url,
            create_track_url(track),
            models.Track(
                name=track.title,
                uri=track.stream_url,
                artists=[artist_tuple.model_artist],
            ),
            track,
        )
        return (artist_tuple, track_tuple)

    @staticmethod
    def create_track_models(
        tracks: List[SingleTrack],
    ) -> List[Tuple[ArtistTuple, TrackTuple]]:
        return list(map(ModelFactory._create_track, tracks))

    @staticmethod
    def create_directory_refs(categories: List[Category]):
        return list(
            map(
                lambda cat: models.Ref.directory(
                    uri=f"hearthis:categories:{cat.id}", name=cat.name
                ),
                categories,
            )
        )
