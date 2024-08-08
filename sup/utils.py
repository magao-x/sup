import xconf
import pathlib
import logging
from typing import Any

import orjson
from starlette.responses import JSONResponse

from .constants import DEFAULT_CONFIG

log = logging.getLogger(__name__)

class OrjsonResponse(JSONResponse):
    def render(self, content: Any) -> bytes:
        return orjson.dumps(content, option=orjson.OPT_SERIALIZE_NUMPY)


@xconf.config
class GUIConfig(xconf.Command):
    """GUI Dashboard Config Command"""
    layout : str = xconf.field(default=DEFAULT_CONFIG["layout"])
    replicated_cameras : list[str] = xconf.field(help="List of cameras", default_factory=lambda: DEFAULT_CONFIG["replicated_cameras"])

    def main(self):
        print('Got this layout:', self.layout)
        return self.config_to_dict()


def parse_config_file(config: dict, config_path: pathlib.Path):
    log.debug(f"Parsing config file {config_path}")
    new_config = {}
    try:
        config_parser = GUIConfig.from_config(config_path_or_paths=[config_path])
        new_config = config_parser.config_to_dict()
    except FileNotFoundError:
        log.warning(f"Config file {config_path} not found.")
    for key, val in new_config.items():
        if key in config.keys():
            config[key] = val
    return config