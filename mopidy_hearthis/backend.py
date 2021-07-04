import logging

import pykka
from mopidy import backend

from .library import HearthisLibraryProvider

logger = logging.getLogger(__name__)


class HeartthisBackend(pykka.ThreadingActor, backend.Backend):
    uri_schemes = ["hearthis"]

    def __init__(self, config, audio):
        super().__init__()
        self.library = HearthisLibraryProvider(backend=self, config=config)
        self.playback = None
        self.playlists = None
