import config
from pymisp import ExpandedPyMISP, MISPEvent
import os
import argparse
import re
import subprocess
import sys

def init(config_file):
    """
    Initialize local directory and parameters, according to the
    config file given at startup.
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
    Initialize the connexion to MISP instance, instantiating an
    ExpandedPyMISP object using the config.
    """
    config.set_ssl(misp_c)
    return ExpandedPyMISP(misp_c["url"],
                          misp_c["key"],
                          misp_c["ssl"])


def cli():
    """
    Initialize script arguments.
    """
    parser = argparse.ArgumentParser(description='Transfer events from \
                                                  SFTP server to misp \
                                                  instance')
    parser.add_argument("-c", "--config",
                        required=False, default="./conf/config.yaml",
                        help="Specify a config file different from default ./conf/config.yaml")
    parser.add_argument("-n", "--no-download",
                        action='store_true',
                        help="If specify, only perfom the upload to misp action")
    return parser.parse_args()


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


def generate_proxy_command(proxy_command, host, host_port, proxy_host, proxy_port):
    """
    Replace every placeholders in the config proxy command with its value,
    in order to create the true command.
    """
    proxy_command = proxy_command.replace("proxy_host", proxy_host, 1)
    proxy_command = proxy_command.replace("proxy_port", str(proxy_port), 1)
    proxy_command = proxy_command.replace("host", host, 1)
    proxy_command = proxy_command.replace("host_port", str(host_port), 1)
    return proxy_command


def get_events(identity_file,
               proxy_command,
               host_ip,
               port,
               user,
               server_dir,
               local_dir, logger):
    """
    Invoke a bash command to get all the file from the sftp server.
    The choice to use subprocess and the bash command was made because of the
    limitation regarding the cipher algorithms available in Paramiko.
    FIXME : Number of file calculation is wrong.
    """
    old_file_number = len([name for name in os.listdir(local_dir) if os.path.isfile(os.path.join(local_dir, name))])
    subprocess.run(["sftp",
                    "-i", f"{identity_file}",
                    f"-o ProxyCommand={proxy_command}",
                    "-P", f"{port}",
                    f"{user}@{host_ip}:{server_dir}/*.json {local_dir}"], check=True)
    new_file_number = len([name for name in os.listdir(local_dir) if os.path.isfile(os.path.join(local_dir, name))])
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
        event = MISPEvent()
        event.load_file(file)
        if event_already_exist(misp, event):
            if not event_not_updated(misp, event):
                rep = misp.update_event(event, pythonify=False)
                logger.info(f"Event {file} updated")
                _event_updated += 1
            else:
                _event_not_updated += 1
                logger.info(f"Event {file} already existing and not updated")
        else:
            rep = misp.add_event(event, pythonify=False)
            if "errors" in rep:
                logger.warning(f"Error on event: {file}")
                logger.warning(rep)
                if rep["errors"][1]["name"] == "Event blocked by event blocklist.":
                    _event_deleted += 1
                else :
                    _event_error += 1
            else:
                logger.info(f"Event {file} added")
                _event_added += 1
    logger.info(f"Total : \
                \n\t {_event_updated} events updated \
                \n\t {_event_added} new events added \
                \n\t {_event_deleted} events not added (in blocklist)\
                \n\t {_event_not_updated} events not updated \
                \n\t {_event_error} errors")


def main():
    """
    main function
    """
    args = cli()
    logger, sftp_c, misp_c = init(args.config)
    misp = misp_init(misp_c)
    proxy_command = ""
    if sftp_c["proxy_command"] != "":
        proxy_command = generate_proxy_command(
                        sftp_c["proxy_command"],
                        sftp_c["host"],
                        sftp_c["port"],
                        sftp_c["proxy_host"],
                        sftp_c["proxy_port"]
                        )

    if not args.no_download:
        get_events(sftp_c["private_key_file"],
                  proxy_command,
                  sftp_c["host"], sftp_c["port"], sftp_c["username"],
                  sftp_c["sftp_directory"], sftp_c["local_directory"], logger)
    upload_events(misp, sftp_c["local_directory"], logger)

if __name__ == "__main__":
    # execute only if run as a script
    main()
