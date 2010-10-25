# Copyright 2010 The Update Framework.  See LICENSE for licensing information.

import logging
logging.raiseExceptions = False

import tuf.conf


FORMAT_STRING = "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s"


logger = logging.getLogger("tuf")
handler = logging.StreamHandler()
formatter = logging.Formatter(FORMAT_STRING)
handler.setFormatter(formatter)
logger.addHandler(handler)


def get_logger():
    return logger


def set_log_level(level):
    logger.setLevel(level)
    handler.setLevel(level)


set_log_level(tuf.conf.settings.log_level)
