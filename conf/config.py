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


def create_logger(config_log):
    with open(config_log["logging_conf"], "r") as log_conf_file:
        log_conf = yaml.safe_load(log_conf_file)
        path, file = os.path.split(log_conf["LOGGING"]["handlers"]["file"]["filename"])
        try:
            os.mkdir(path)
        except FileExistsError:
            pass
        except:
            print("Unexpected error: ", sys.exc_info()[0])
            raise
        logging.config.dictConfig(log_conf["LOGGING"])
        logger = logging.getLogger("__name__")
        logger.info("Configuration file loading completed")
        logging.captureWarnings(True)
        return logger


def set_ssl(misp_c):
    if misp_c["ssl"]:
        os.environ["REQUESTS_CA_BUNDLE"] = misp_c["CA_BUNDLE"]
