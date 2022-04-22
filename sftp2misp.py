import conf.config as config
from pymisp import ExpandedPyMISP, MISPEvent
import pymisp.exceptions
import os
import argparse
import re
import subprocess
import sys
import warnings

warnings.filterwarnings("once")


def init(args):
    """
    Initialize local directory and parameters, according to the
    config file given at startup.
    """
    sftp_c, misp_c, misc_c = config.get_config(args.config)
    logger = config.get_logger(
        misc_c["logging_conf"], misc_c["logging_directory"], misc_c["logging_suffix"]
    )
    check_args(args, logger)
    try:
        os.mkdir(misc_c["local_directory"])
    except FileExistsError:
        if args.delete_local_directory_content:
            logger.info("Deleting local directory content")
            for root, dirs, files in os.walk(misc_c["local_directory"]):
                for file in files:
                    os.remove(os.path.join(root, file))
        else:
            pass
    except:
        logger.error(f"Unexpected error on local filesystem: {sys.exc_info()[0]}")
        exit(1)
    return logger, sftp_c, misp_c, misc_c


def misp_init(misp_c, logger):
    """
    Initialize the connexion to MISP instance, instantiating an
    ExpandedPyMISP object using the config.
    """
    config.set_ssl(misp_c)
    try:
        return ExpandedPyMISP(misp_c["url"], misp_c["key"], misp_c["ssl"])
    except pymisp.exceptions.PyMISPError as err:
        logger.error(err)
        exit(1)


def cli():
    """
    Initialize script arguments.
    """
    parser = argparse.ArgumentParser(
        description="Automation script to download \
                                                  JSON MISP files from a SFTP \
                                                  server and import them via \
                                                  API to a MISP instance."
    )
    parser.add_argument(
        "-c",
        "--config",
        required=False,
        default="./conf/config.yaml",
        help="Specify CONFIG as an alternative configuration file to ./conf/config.yaml",
    )
    parser.add_argument(
        "-n",
        "--no-download",
        action="store_true",
        help="If specified, bypass JSON MISP files download, and just import the local JSON MISP files into MISP instance",
    )
    parser.add_argument(
        "-d",
        "--delete-local-directory-content",
        action="store_true",
        help=" If specified, erase the content of the local_directory before JSON MISP files are downloaded",
    )
    parser.add_argument('-v', '--verbose', action='count', default=0)

    return parser.parse_args()


def check_args(args, logger):
    if args.delete_local_directory_content and args.no_download:
        print("\t\t\t\33[6m \033[1m \33[35m ಠ_ಠ huh \033[0m")
        logger.warning(
            "Options no-download and delete_local_directory_content are incompatible"
        )
        exit(1)


def event_already_exist(misp, event) -> bool:
    """
    Test if the current event already exists in MISP.
    """
    event_uuid = event.get("uuid")
    return misp.event_exists(event_uuid)


def event_not_updated(misp, local_event) -> bool:
    """
    Test if the downloaded version of the current event was updated compared
    to the version on the MISP instance.
    """
    local_event_uuid = local_event.get("uuid")
    local_event_timestamp = local_event.get("timestamp")
    misp_event = misp.get_event(local_event_uuid, pythonify=True)
    misp_event_timestamp = misp_event.get("timestamp")
    return local_event_timestamp == misp_event_timestamp


def generate_proxy_command(proxy_command, host, host_port, proxy_host, proxy_port, logger):
    """
    Replace every placeholders in the config proxy command with its value,
    in order to create the true command.
    """
    proxy_command = proxy_command.replace("proxy_host", proxy_host, 1)
    proxy_command = proxy_command.replace("proxy_port", str(proxy_port), 1)
    proxy_command = proxy_command.replace("host", host, 1)
    proxy_command = proxy_command.replace("host_port", str(host_port), 1)
    logger.debug(f"returned proxy command {proxy_command}")
    return proxy_command


def get_events(
    identity_file, proxy_command, host_ip, port, user, server_dir, local_dir, logger
):
    """
    Invoke a bash command to get all the file from the sftp server.
    The choice to use subprocess and the bash command was made because of the
    limitation regarding the cipher algorithms available in Paramiko.
    FIXME : Number of file calculation is "wrong".
    """
    old_file_number = len(
        [
            name
            for name in os.listdir(local_dir)
            if os.path.isfile(os.path.join(local_dir, name))
        ]
    )
    proc = subprocess.run(
        [
            "sftp",
            "-i",
            f"{identity_file}",
            f"-o ProxyCommand={proxy_command}",
            "-P",
            f"{port}",
            f"{user}@{host_ip}:{server_dir}/*.json {local_dir}",
        ],
        check=True,
    )
    print(proc)
    new_file_number = len(
        [
            name
            for name in os.listdir(local_dir)
            if os.path.isfile(os.path.join(local_dir, name))
        ]
    )
    logger.info(f"{new_file_number-old_file_number} events downloaded")


def upload_events(misp, local_dir, logger):
    """
    For each events in the local_dir directory, instantiate a new MISPEvent
    object, and try pushing it to MISP.
    We monitor what happens to events, if they got deleted on misp, if
    they got updated since last upload, or if they are new.
    """
    _event_updated = 0
    _event_not_updated = 0
    _event_added = 0
    _event_deleted = 0
    _event_error = 0
    for filename in os.listdir(local_dir):
        file = os.path.join(local_dir, filename)
        if file.endswith(".json"):
            event = MISPEvent()
            event.load_file(file)
            logger.info(f"Loading {file}")
            if event_already_exist(misp, event):
                if not event_not_updated(misp, event):
                    rep = misp.update_event(event, pythonify=False)
                    logger.info(f"Event {file} updated")
                    _event_updated += 1
                else:
                    _event_not_updated += 1
                    logger.info(f"Event {file} already existing and not updated")
            else:
                try:
                    rep = misp.add_event(event, pythonify=False)
                    if "errors" in rep:
                        logger.warning(f"Error on event: {file}")
                        logger.warning(rep)
                        if (
                            rep["errors"][1]["name"]
                            == "Event blocked by event blocklist."
                        ):
                            _event_deleted += 1
                        else:
                            _event_error += 1
                    else:
                        logger.info(f"Event {file} added")
                        _event_added += 1
                except pymisp.exceptions.MISPServerError:
                    logger.warning(f"Server error on event {file}")
                    _event_error += 1
    logger.info(
        "Total : "
        f"\n{' '*62} {_event_updated} events updated"
        f"\n{' '*62} {_event_added} new events added"
        f"\n{' '*62} {_event_deleted} events not added (in blocklist)"
        f"\n{' '*62} {_event_not_updated} events not updated"
        f"\n{' '*62} {_event_error} errors"
    )


def main():
    """
    main function
    """
    args = cli()
    logger, sftp_c, misp_c, misc_c = init(args)
    print(args.verbose)
    misp = misp_init(misp_c, logger)
    proxy_command = ""
    if sftp_c["proxy_command"] != "":
        proxy_command = generate_proxy_command(
            sftp_c["proxy_command"],
            sftp_c["host"],
            sftp_c["port"],
            sftp_c["proxy_host"],
            sftp_c["proxy_port"],
            logger
        )
    if not args.no_download:
        for sftp_directory in sftp_c["sftp_directories"]:
            logger.info(f"Downloading events from {sftp_directory}")
            get_events(
                sftp_c["private_key_file"],
                proxy_command,
                sftp_c["host"],
                sftp_c["port"],
                sftp_c["username"],
                sftp_directory,
                misc_c["local_directory"],
                logger,
            )
    upload_events(misp, misc_c["local_directory"], logger)


if __name__ == "__main__":
    # execute only if run as a script
    main()
