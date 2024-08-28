import xconf
import pathlib
import logging
from typing import Any

import orjson
from starlette.responses import JSONResponse

log = logging.getLogger(__name__)

class OrjsonResponse(JSONResponse):
    def render(self, content: Any) -> bytes:
        return orjson.dumps(content, option=orjson.OPT_SERIALIZE_NUMPY)

def orjson_to_utf8(obj):
    buf = orjson.dumps(obj, option=orjson.OPT_SERIALIZE_NUMPY)
    return buf.decode('utf8')
