import pathlib
CONFIG_PATH = pathlib.Path("/opt/MagAOX/config")
REPLICATED_CAMERAS = [
    'camsci1',
    'camsci2',
    'camwfs',
    # 'camlowfs',
    'camtip',
    # 'camacq',
]
TMPFILE_ROOT = pathlib.Path("/dev/shm")