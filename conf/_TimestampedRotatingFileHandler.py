"""
Rotating File Handler (as of logging.handlers.RotatingFileHandler) that
also create a different file every day, with date in filename.
By default, keeps logs file 30 days.
"""

import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
import re

class TimestampedRotatingFileHandler(logging.handlers.RotatingFileHandler):
    def __init__(
        self,
        filename,
        mode="a",
        maxBytes=0,
        dateFormat="%Y%m%d",
        keepUntil=30,
        backupCount=0,
        encoding=None,
        delay=False,
    ):
        file, extension = os.path.splitext(filename)
        path, filen = os.path.split(file)
        now = datetime.now()
        delete_date = (now - timedelta(days=keepUntil)).strftime(dateFormat)
        filename = f"{path}/{now.strftime(dateFormat)}_{filen}{extension}"
        for to_delete in Path(path).rglob(f"*{filen}*"):
            delete_file = (os.path.split(os.path.splitext(to_delete)[0]))[1]
            match = re.search(r'\d{8}', delete_file)
            if match:
            	old_date = datetime.strptime(match.group(), '%Y%m%d').strftime(dateFormat)
            	if old_date < delete_date:
                	os.remove(to_delete)
        logging.handlers.RotatingFileHandler.__init__(
            self, filename, mode, maxBytes, backupCount, encoding, delay
        )
