from enum import Enum
import pathlib

TMPFILE_ROOT = pathlib.Path("/dev/shm")
INSTRUMENT_CONFIG_ROOT = pathlib.Path("/opt/MagAOX/config")
CONFIG_FILENAME = "gui_sup.conf"

INSTGRAPH_FILE_PATH = "/tmp/magaox.drawio"

# The audibleAlerts device (INDI name maggieo_x) copies or synthesizes every
# clip it plays into this directory and publishes the path relative to it as
# maggieo_x.playback.file, which is what the browser player fetches.
AUDIBLE_ALERTS_DEVICE = "maggieo_x"
AUDIBLE_ALERTS_CACHE_ROOT = "/tmp/audibleAlerts_cache"
# Subdirectory of the above holding speech whose text was substituted at
# playback time. The device wipes it on startup, so clips there are one-offs.
AUDIBLE_ALERTS_TEMP_SUBDIR = "temp"
AUDIBLE_ALERTS_CLIP_MAX_AGE_SEC = 365 * 24 * 60 * 60

SITE_LOCATION = "Las Campanas Observatory"
OBS_ROOT = "/home/guestobs/obs"
BATCH_UPDATE_INTERVAL = 0.2 # seconds

class InstrumentLayouts(Enum):
    MAGAOX = "magaox"
    SCOOB = "scoob"
# Severities a log message can open with, as the web UI's level filters name
# them. Devices pad the shorter ones to four characters ("ERR  ...").
LOG_LEVELS = ("EMER", "ALRT", "CRIT", "ERR", "WARN", "NOTE", "INFO")
