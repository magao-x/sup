import pathlib

import json

with open('../constants.json', 'r') as file:
    constants = json.load(file)

INDI_HOST = constants["INDI_HOST"]
INDI_PORT = constants["INDI_PORT"]
POTEMKIN = constants["POTEMKIN"]
CONFIG_PATH = pathlib.Path(constants["CONFIG_PATH"])
REPLICATED_CAMERAS = constants["REPLICATED_CAMERAS"]
DEFAULT_LAYOUT = constants["DEFAULT_LAYOUT"]
TMPFILE_ROOT = pathlib.Path(constants["TMPFILE_ROOT"])

SITE_LOCATION = constants["SITE_LOCATION"]
BATCH_UPDATE_INTERVAL = constants["BATCH_UPDATE_INTERVAL"] # second
PING_INTERVAL = constants["PING_INTERVAL"]
MAGAOX_DEFAULT_ROLE = constants["MAGAOX_DEFAULT_ROLE"]
CONFIG_FILE = constants["CONFIG_FILE"]
