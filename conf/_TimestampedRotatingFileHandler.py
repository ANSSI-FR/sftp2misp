"""
Rotating File Handler (as of logging.handlers.RotatingFileHandler) that
also create a different file every day, with date in filename.
"""

import os
import logging
from datetime import datetime


class TimestampedRotatingFileHandler(logging.handlers.RotatingFileHandler):
    def __init__(
        self,
        filename,
        mode="a",
        maxBytes=0,
        date="%Y%m%d",
        backupCount=0,
        encoding=None,
        delay=False,
    ):
        filename, extension = os.path.splitext(filename)
        path, filename = os.path.split(filename)
        filename = f"{path}/{datetime.now().strftime(date)}_{filename}{extension}"
        logging.handlers.RotatingFileHandler.__init__(
            self, filename, mode, maxBytes, backupCount, encoding, delay
        )
