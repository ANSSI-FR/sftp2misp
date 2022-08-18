"""
Configuration module for sftp2misp script
"""
import logging
import logging.config
import os
import sys
import yaml
from pathlib import Path


def check_config(config):
    """
    Check compliance of given config file
    """
    sftp_entries = {
        "host": str,
        "port": int,
        "sftp_directories": list,
        "username": str,
        "private_key_file": str,
        "proxy_command": str,
        "proxy_host": str,
        "proxy_port": int,
    }
    misp_entries = {
        "url": str,
        "key": str,
        "bypass_proxy": bool,
        "ssl": bool,
        "CA_BUNDLE": str,
    }
    misc_entries = {"local_directory": str, "logging_conf": str}
    super_map = [sftp_entries, misp_entries, misc_entries]
    super_super_map = ["SFTP", "MISP", "MISC"]
    error = []
    for i, item in enumerate(super_map):
        for entry in item:
            if entry not in config[super_super_map[i]]:
                error.append(f"{entry} of config.yaml.template is not in your config")
            elif type(config[super_super_map[i]][entry]) != item[entry]:
                error.append(
                    f"{type(config[super_super_map[i]][entry])} is not {item[entry]}"
                )
        for entry in config[super_super_map[i]]:
            if not entry in item:
                error.append(f"{entry} of your config is not in config.yaml.template")
    return error


def get_config(config_file):
    """
    Open, load and check for errors in configuration file
    """
    cwd = Path(__file__).parent.parent
    config_path = cwd / Path(config_file)
    try:
        with open(config_path, "r") as config_file:
            conf = yaml.safe_load(config_file)
            errors = check_config(conf)
            if errors:
                entry = ["List of entries", "Entry"]
                print(
                    f"Your configuration file {conf_file} is not compliant with config.yaml.template : entries are missing or not supported. Please review and fix it."
                )
                print(f"{entry[len(errors) == 1]} not compliant :")
                for error in errors:
                    print(error)
                sys.exit(1)
            return conf["SFTP"], conf["MISP"], conf["MISC"]
    except FileNotFoundError as _:
        print(f"Configuration file \"{conf_file}\" ({config_path}) not found")
        sys.exit(1)



def create_logger(config_log):
    """
    Open and load configuration file for logging
    """
    with open(config_log["logging_conf"], "r") as log_conf_file:
        log_conf = yaml.safe_load(log_conf_file)
        path, _ = os.path.split(log_conf["LOGGING"]["handlers"]["file"]["filename"])
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
    """
    Set environnment variable in order to use https communication
    """
    if misp_c["ssl"]:
        os.environ["REQUESTS_CA_BUNDLE"] = misp_c["CA_BUNDLE"]
