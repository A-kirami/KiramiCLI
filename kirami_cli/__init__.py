from importlib.metadata import EntryPoint, entry_points, version

from cashews import Cache  # type: ignore

from .i18n import _ as _

try:
    __version__ = version("kirami-cli")
except Exception:
    __version__ = None

cache = Cache("kirami-cli")
cache.setup("mem://")

from .cli import cli as cli_sync
from .cli import run_sync
from .consts import PLUGINS_GROUP
from .handlers import install_signal_handler


def load_plugins():
    entrypoint: EntryPoint
    for entrypoint in entry_points(group=PLUGINS_GROUP):
        entrypoint.load()()  # type: ignore


async def cli_main(*args, **kwargs):
    install_signal_handler()
    load_plugins()
    return await run_sync(cli_sync)(*args, **kwargs)
