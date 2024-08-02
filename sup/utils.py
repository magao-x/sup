import xconf

from typing import Any

import orjson
from starlette.responses import JSONResponse


class OrjsonResponse(JSONResponse):
    def render(self, content: Any) -> bytes:
        return orjson.dumps(content, option=orjson.OPT_SERIALIZE_NUMPY)

@xconf.config
class GUIConfig(xconf.Command):
    """Demo command"""
    layout : str = xconf.field(default='MAGAOX')

    def main(self):
        breakpoint()
        print('Got this layout:', self.layout)
        return self.config_to_dict()