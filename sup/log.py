import logging
logger = logging.getLogger('sup')
debug = logger.debug
info = logger.info
warn = logger.warn
error = logger.error
critical = logger.critical

def set_log_level(level):
    logger.setLevel(level)
