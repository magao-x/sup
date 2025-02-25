from enum import Enum
import pathlib

TMPFILE_ROOT = pathlib.Path("/dev/shm")
INSTRUMENT_CONFIG_ROOT = pathlib.Path("/opt/MagAOX/config")
CONFIG_FILENAME = "gui_sup.conf"

INSTGRAPH_FILE_PATH = "/opt/MagAOX/source/instGraph/demo/demo2.drawio"

SITE_LOCATION = "Las Campanas Observatory"
BATCH_UPDATE_INTERVAL = 0.2 # seconds

class InstrumentLayouts(Enum):
    MAGAOX = "magaox"
    SCOOB = "scoob"
