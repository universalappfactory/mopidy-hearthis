import logging
import pathlib

from mopidy import config, ext

__version__ = "0.2.3"
logger = logging.getLogger(__name__)


class Extension(ext.Extension):

    dist_name = "Mopidy-Hearthis"
    ext_name = "hearthis"
    version = __version__

    def get_default_config(self):
        return config.read(pathlib.Path(__file__).parent / "ext.conf")

    def get_config_schema(self):
        schema = super().get_config_schema()
        schema["username"] = config.String(optional=True)
        schema["password"] = config.Secret(optional=False)
        return schema

    def setup(self, registry):
        from .backend import HeartthisBackend

        registry.add("backend", HeartthisBackend)
