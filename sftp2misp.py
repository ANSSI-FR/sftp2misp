"""Automation script to download JSON MISP files from a SFTP
   server and import them via API to a MISP instance."""
import os
import argparse
import subprocess
import sys
import logging
import warnings
import json
from pymisp import ExpandedPyMISP, MISPEvent
import pymisp.exceptions
from conf import config


def init(args):
    """
    Initialize local directory and parameters, according to the
    config file given at startup.
    """
    sftp_c, misp_c, misc_c = config.get_config(args.config)
    logger = config.create_logger(misc_c)
    check_args(args, logger)
    try:
        os.mkdir(misc_c["local_directory"])
    except FileExistsError:
        if args.delete_local_directory_content:
            logger.info("Deleting local directory content")
            for root, _, files in os.walk(misc_c["local_directory"]):
                for file in files:
                    os.remove(os.path.join(root, file))
        else:
            pass
    return logger, sftp_c, misp_c, misc_c


def misp_init(misp_c, logger):
    """
    Initialize the connection to MISP instance, instantiating an
    ExpandedPyMISP object using the config.
    """
    config.set_ssl(misp_c)
    try:
        if misp_c["bypass_proxy"]:
            return ExpandedPyMISP(
                misp_c["url"],
                misp_c["key"],
                misp_c["ssl"],
                proxies={"http": None, "https": None},
            )
        return ExpandedPyMISP(misp_c["url"], misp_c["key"], misp_c["ssl"])
    except pymisp.exceptions.PyMISPError as err:
        logger.error(err)
        sys.exit(1)


def cli():
    """
    Initialize script arguments.
    """
    parser = argparse.ArgumentParser(
        description="""Automation script to download JSON MISP files from a SFTP
                       server and import them via API to a MISP instance."""
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
        help="""Bypass JSON MISP files download, and just import the
                local JSON MISP files into MISP instance""",
    )
    parser.add_argument(
        "-d",
        "--delete-local-directory-content",
        action="store_true",
        help="""Erase the content of the local_directory
                before JSON MISP files are downloaded""",
    )
    parser.add_argument(
        "-y",
        "--yara",
        action="store_true",
        help="""Also download YARA files on server"""
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="""Enable verbose mode"""
    )
    # parser.add_argument(
    #     "-i",
    #     "--diff",
    #     required=False,
    #     help="Run a diff",
    # )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Reduce spam in logs by showing warnings only once",
    )

    return parser.parse_args()


def check_args(args, logger):
    """
    Check for incompatible arguments
    """
    if args.delete_local_directory_content and args.no_download:
        print("\t\t\t\33[6m \033[1m \33[35m ಠ_ಠ huh \033[0m")
        logger.warning(
            "Options no-download and delete_local_directory_content are incompatible"
        )
        sys.exit(1)


def event_already_exist(misp, event) -> bool:
    """
    Test if the current event already exists in MISP.
    """
    event_uuid = event.get("uuid")
    return misp.event_exists(event_uuid)


def event_not_updated(misp, local_event, logger) -> bool:
    """
    Test if the downloaded version of the current event was updated compared
    to the version on the MISP instance.
    """
    local_event_uuid = local_event.get("uuid")
    local_event_timestamp = local_event.get("timestamp")
    misp_event = misp.get_event(local_event_uuid, pythonify=True)
    misp_event_timestamp = misp_event.get("timestamp")
    logger.debug(f"Event uuid : {local_event_uuid}")
    logger.debug(f"Local timestamp : {local_event_timestamp}")
    logger.debug(f"MISP Event timestamp : {misp_event_timestamp}")
    return local_event_timestamp == misp_event_timestamp


def generate_proxy_command(
    proxy_command, host, host_port, proxy_host, proxy_port, logger
):
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


def sftp_get_files(
    identity_file, proxy_command, host_ip, port, user, server_dir, local_dir, extension, logger
):
    try:
        ret = subprocess.run(
            [
                "sftp",
                "-i",
                f"{identity_file}",
                f"-o ProxyCommand={proxy_command}",
                "-P",
                f"{port}",
                f"{user}@{host_ip}:{server_dir}/*.{extension} {local_dir}",
            ],
            check=True,
        )
    except subprocess.CalledProcessError as err:
        return 1
    else:
        return 0


def get_events(
    identity_file, proxy_command, host_ip, port, user, server_dir, local_dir, extensions, logger
):
    """
    Invoke a bash command to get all the files from the sftp server.
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
    errors = 0
    logger.debug(f"extension list {extensions}")
    for extension in extensions:
        logger.debug(f"downloading .{extension} files on server {host_ip}")
        errors += sftp_get_files(identity_file, proxy_command, host_ip, port, user, server_dir, local_dir, extension, logger)
    if errors >= len(extensions):
        logger.error("Unable to retrieve files from sftp server, please verify the configuration file")
        sys.exit(1)
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
    For each event in the local_dir directory, instantiate a new MISPEvent
    object, and try pushing it to MISP.
    We monitor what happens to events, if they got deleted on MISP, if
    they got updated since last upload, or if they are new.
    """
    _event_updated = 0
    _event_not_updated = 0
    _event_added = 0
    _event_deleted = 0
    _event_error = 0
    _wrong_format = 0
    for filename in os.listdir(local_dir):
        file = os.path.join(local_dir, filename)
        if file.endswith(".json"):
            event = MISPEvent()
            logger.info(f"Loading {file}")
            try:
                event.load_file(file)
            except (json.decoder.JSONDecodeError, pymisp.exceptions.NewEventError, pymisp.exceptions.PyMISPError) as err:
                logger.warning(err)
                logger.info(f"{filename} is not in JSON-MISP format")
                _wrong_format += 1
                continue

            if event_already_exist(misp, event):
                if not event_not_updated(misp, event, logger):
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
        f"\n{' '*62} {_wrong_format} files not compliant with MISP JSON format"
        f"\n{' '*62} {_event_error} errors (check loggers WARNING and ERRORS)"
    )


def main():
    """
    main function
    """
    args = cli()
    logger, sftp_c, misp_c, misc_c = init(args)
    if args.verbose:
        logger.setLevel(1)
        logger.info("verbose mode")
    if args.quiet:
        warnings.filterwarnings("once")
    else:
        warnings.filterwarnings("always")
    misp = misp_init(misp_c, logger)
    proxy_command = ""
    extensions = ["json"]
    if args.yara:
        extensions.append("yara")

    if sftp_c["proxy_command"] != "":
        proxy_command = generate_proxy_command(
            sftp_c["proxy_command"],
            sftp_c["host"],
            sftp_c["port"],
            sftp_c["proxy_host"],
            sftp_c["proxy_port"],
            logger,
        )
    if not args.no_download:
        for sftp_directory in sftp_c["sftp_directories"]:
            logger.info("Downloading events from %s", sftp_directory)
            get_events(
                sftp_c["private_key_file"],
                proxy_command,
                sftp_c["host"],
                sftp_c["port"],
                sftp_c["username"],
                sftp_directory,
                misc_c["local_directory"],
                extensions,
                logger,
            )
    upload_events(misp, misc_c["local_directory"], logger)


if __name__ == "__main__":
    # execute only if run as a script
    main()
