import pathlib

INDI_HOST = "127.0.0.1"
INDI_PORT = 7624
POTEMKIN = False

TMPFILE_ROOT = pathlib.Path("/dev/shm")
CONFIG_PATH = pathlib.Path("/opt/MagAOX/config")
CONFIG_FILE = "gui_sup.conf"

SITE_LOCATION = "Las Campanas Observatory"
BATCH_UPDATE_INTERVAL = 0.2 # seconds
PING_INTERVAL = 10
MAGAOX_DEFAULT_ROLE = "workstation"

MAGAOX = "magaox"
SCOOB = "scoob"
LAYOUT_OPTIONS = [MAGAOX, SCOOB]
DEFAULT_CONFIG = {
        "layout": MAGAOX,
        "replicated_cameras": [ "camsci1", "camsci2", "camwfs", "camtip" ]
    }
