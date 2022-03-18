import config
from pymisp import ExpandedPyMISP, MISPEvent, MISPAttribute
import paramiko
import os
import json
import argparse
from getpass import getpass
import asyncio, asyncssh, sys

import asyncio
import stat

import aiosocks
import asyncssh
from asyncssh import SFTPClient

import subprocess
import sys

def init(config_file):
    """
    init local directory to download event files from ftp server
    """
    sftp_c, misp_c, misc_c = config.get_config(config_file)
    logger = config.get_logger(misc_c["logging_conf"], misc_c["logging_file"])
    try:
        os.mkdir(sftp_c["local_directory"])
    except FileExistsError:
        pass
    except:
        logger.info("Unexpected error: %s", sys.exc_info()[0])
        raise
    return logger, sftp_c, misp_c


def misp_init(misp_c):
    """
    init connexion to misp instance
    """
    config.set_ssl(misp_c)
    return ExpandedPyMISP(misp_c["url"],
                          misp_c["key"],
                          misp_c["ssl"])


def cli():
    parser = argparse.ArgumentParser(description='Transfer event from sftp to misp')
    parser.add_argument("-c", "--config",
                        required=False, default="./conf/config.yaml",
                        help="Fichier de configuration différent de config.yaml")
    return parser.parse_args()


def event_already_exist(misp, event) -> bool:
    """
    check if event is already on misp instance
    """
    event_uuid = event.get("uuid")
    return misp.event_exists(event_uuid)


def event_not_updated(misp, local_event) -> bool:
    """
    check if event has been updated since last upload
    """
    local_event_uuid = local_event.get("uuid")
    local_event_timestamp = local_event.get("timestamp")
    misp_event = misp.get_event(local_event_uuid, pythonify=True)
    misp_event_timestamp = misp_event.get("timestamp")
    return local_event_timestamp == misp_event_timestamp


def event_deleted(misp, event) -> bool:
    blocklist = misp.event_blocklists()
    event_uuid = event.get("uuid")
    for ev in blocklist:
        if ev.get("event_uuid") == event_uuid:
            return True
    return False


def get_events(identity_file,
               proxy_command,
               ip,
               port,
               user,
               server_dir,
               local_dir):
    subprocess.run(["sftp",
                    "-i", f"{identity_file}",
                    f"-o ProxyCommand={proxy_command}",
                    "-P", f"{port}",
                    f"{user}@{ip}:{server_dir}/5dd*.json {local_dir}"])


def upload_events(misp, logger):
    """

    """
    _event_updated = 0
    _event_not_updated = 0
    _event_added = 0
    _event_deleted = 0
    local_ouput = "output"
    for filename in os.listdir(local_ouput):
        file = os.path.join(local_ouput, filename)
        event = MISPEvent()
        event.load_file(file)
        if event_already_exist(misp, event):
            if not event_not_updated(misp, event):
                misp.update_event(event, pythonify=True)
                logger.info("Event %s updated", file)
                _event_updated += 1
            else:
                _event_not_updated += 1
                logger.info("Event %s was not updated", file)
        elif event_deleted(misp, event):
            _event_deleted += 1
            logger.info("Event %s is in blocklist", file)
        else:
            misp.add_event(event, pythonify=False)
            logger.info("Event %s added", file)
            _event_added += 1
    logger.info(f"Total : \
                \n\t {_event_updated} events mis à jour \
                \n\t {_event_added} events ajoutés \
                \n\t {_event_deleted} events non ajoutés car dans la blocklist (supprimé précédemment) \
                \n\t {_event_not_updated} events non mis à jour")


def main():
    """
    main
    """
    args = cli()
    logger, sftp_c, misp_c = init(args.config)
    misp = misp_init(misp_c)
    get_events(sftp_c["private_key_file"],
               sftp_c["proxy_command"],
               sftp_c["host"], sftp_c["port"], sftp_c["username"],
               sftp_c["sftp_directory"], sftp_c["local_directory"])
    upload_events(misp, logger)

if __name__ == "__main__":
    # execute only if run as a script
    main()
