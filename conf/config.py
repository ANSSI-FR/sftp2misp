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
    misc_entries = {
        "local_directory": str,
        "logging_conf": str
    }
    check_entries = [sftp_entries, misp_entries, misc_entries]
    config_entries = ["SFTP", "MISP", "MISC"]
    error = []
    for i, group in enumerate(check_entries):
        for entry in group:
            if entry not in config[config_entries[i]]:
                error.append(f"\tentry \"{entry}\" of config.yaml.template is not in your config file")
            elif type(config[config_entries[i]][entry]) != group[entry]:
                error.append(
                    f"\tentry \"{entry}\" has type {type(config[config_entries[i]][entry])} but needs to be of type {group[entry]}"
                )
        for entry in config[config_entries[i]]:
            if not entry in group:
                error.append(f"\tentry \"{entry}\" of your config file is not in config.yaml.template")
    return error


def get_config(config_file):
    """
    Open, load and check for errors in configuration file
    """
    config_file = Path(config_file).resolve()
    try:
        with open(config_file, "r") as config_file:
            conf = yaml.safe_load(config_file)
            errors = check_config(conf)
            if errors:
                entry = ["List of entries", "Entry"]
                print(
                    f"Your configuration file {config_file.name} is not compliant with config.yaml.template : entries are missing or not supported. Please review and fix it."
                )
                print(f"{entry[len(errors) == 1]} not compliant :")
                for error in errors:
                    print(error)
                sys.exit(1)
            return conf["SFTP"], conf["MISP"], conf["MISC"]
    except FileNotFoundError as _:
        print(f"Configuration file \"{config_file}\" not found")
        sys.exit(1)



def create_logger(config_log):
    """
    Open and load configuration file for logging
    """
    logging_path = Path(__file__).parent.parent / Path(config_log["logging_conf"])
    try:
        with open(logging_path, "r") as log_conf_file:
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
    except FileNotFoundError as _:
        print(f"Configuration file \"{logging_path}\" not found")
        sys.exit(1)

def set_ssl(misp_c):
    """
    Set environnment variable in order to use https communication
    """
    if misp_c["ssl"]:
        os.environ["REQUESTS_CA_BUNDLE"] = misp_c["CA_BUNDLE"]
