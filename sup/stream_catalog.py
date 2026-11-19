"""The shmims there are to watch, and how to show each.

rtimv, the instrument's image viewer, has a config per camera,
``rtimv_<name>.conf`` in the instrument config directory. Each names the
image's shmim and, optionally, the dark to subtract from it, a saturation
mask, and the level at which it saturates::

    satLevel=16383

    [image]
    key=camwfs

    [dark]
    key=camwfs_dark

    [satMask]
    key=camwfs_sat

Those configs define the catalog's streams first. Any other shmim in the
shmim directory is added after, without a dark or saturation information,
unless some config uses it as a dark or saturation mask: those are excluded,
being parts of another stream rather than images to watch in themselves.
"""
import configparser
import dataclasses
import logging
import pathlib

from .shmim import list_shmims

log = logging.getLogger(__name__)

RTIMV_CONFIG_GLOB = "rtimv_*.conf"
# rtimv's settings before the first section belong to none, which
# configparser doesn't allow; they are read as this section's instead.
TOP_LEVEL_SECTION = "__top__"


@dataclasses.dataclass(frozen=True)
class StreamInfo:
    name : str
    dark : str | None = None
    sat_mask : str | None = None
    sat_level : float | None = None
    # The rtimv config that defined the stream, if one did.
    config : str | None = None


@dataclasses.dataclass(frozen=True)
class StreamCatalog:
    # In order: those from rtimv configs, by config file name, then the rest by name.
    streams : dict[str, StreamInfo]
    # Darks and saturation masks of streams, not listed themselves.
    excluded : frozenset[str]

    def to_json(self):
        return {
            "streams": [dataclasses.asdict(info) for info in self.streams.values()],
            "excluded": sorted(self.excluded),
        }


def _number(text):
    try:
        return int(text)
    except ValueError:
        return float(text)


def read_rtimv_config(path):
    """The stream an rtimv config describes, or None if it names no image."""
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    parser.optionxform = str
    parser.read_string(f"[{TOP_LEVEL_SECTION}]\n" + path.read_text(), source=str(path))
    name = parser.get("image", "key", fallback=None)
    if not name:
        return None
    sat_level = parser.get(TOP_LEVEL_SECTION, "satLevel", fallback=None)
    return StreamInfo(
        name=name,
        dark=parser.get("dark", "key", fallback=None) or None,
        sat_mask=parser.get("satMask", "key", fallback=None) or None,
        sat_level=_number(sat_level) if sat_level else None,
        config=path.name,
    )


def build_catalog(rtimv_config_dir=None, shmim_dir=None):
    """Streams from the rtimv configs in ``rtimv_config_dir``, then the
    other shmims in ``shmim_dir`` (by default, where ImageStreamIO keeps
    them) that aren't any stream's dark or saturation mask. Either source
    may be missing."""
    streams = {}
    excluded = set()
    config_paths = sorted(pathlib.Path(rtimv_config_dir).glob(RTIMV_CONFIG_GLOB)) if rtimv_config_dir else []
    for path in config_paths:
        try:
            info = read_rtimv_config(path)
        except (OSError, configparser.Error, ValueError) as e:
            log.warning(f"Skipping rtimv config {path}: {e}")
            continue
        if info is None:
            log.debug(f"rtimv config {path} names no image")
            continue
        if info.name in streams:
            log.warning(f"Stream {info.name} in {path.name} is already defined by {streams[info.name].config}; skipping")
            continue
        streams[info.name] = info
        excluded.update(companion for companion in (info.dark, info.sat_mask) if companion)
    # A stream one config defines and another uses as a dark is a dark.
    for name in excluded & streams.keys():
        log.debug(f"Stream {name} from {streams[name].config} is used as a dark or saturation mask; not listing it")
        del streams[name]
    for name in list_shmims(shmim_dir):
        if name not in streams and name not in excluded:
            streams[name] = StreamInfo(name=name)
    log.info(f"Found {len(streams)} streams to serve ({len(config_paths)} rtimv configs read, {len(excluded)} darks and saturation masks excluded)")
    return StreamCatalog(streams=streams, excluded=frozenset(excluded))
