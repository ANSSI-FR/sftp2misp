import logging
import logging.config
import os
import sys
import datetime
import yaml


def get_config(conf_file):
    with open(conf_file, "r") as config_file:
        conf = yaml.safe_load(config_file)
        return conf["SFTP"], conf["MISP"], conf["MISC"]


def get_logging_config(log_conf_file):
    with open(log_conf_file, "r") as log_conf:
        return yaml.safe_load(log_conf)


def get_logger(log_conf_file, log_directory, log_suffix):
    try:
        os.mkdir(log_directory)
    except FileExistsError:
        pass
    except:
        print("Unexpected error: ", sys.exc_info()[0])
        raise
    now = datetime.datetime.now()
    if log_directory[-1] != "/":
        log_directory += "/"
    filename = now.strftime(f"{log_directory}%Y%m%d_{log_suffix}")
    logging.config.dictConfig(get_logging_config(log_conf_file)["LOGGING"])
    file_handler = logging.handlers.RotatingFileHandler(
        filename, "a", maxBytes=10485760, backupCount=20, encoding="utf8"
    )
    file_handler.setLevel(1)
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s.%(funcName)s(): %(message)s"
    )
    file_handler.setFormatter(formatter)

    logger = logging.getLogger()
    for hdlr in logger.handlers[:]:
        if isinstance(hdlr, logging.FileHandler):
            logger.removeHandler(hdlr)
    logger.addHandler(file_handler)
    logger.info("Configuration file loading completed")
    logging.captureWarnings(True)
    return logger


def set_ssl(misp_c):
    if misp_c["ssl"]:
        os.environ["REQUESTS_CA_BUNDLE"] = misp_c["CA_BUNDLE"]
