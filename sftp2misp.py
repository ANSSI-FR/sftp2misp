import config
from pymisp import ExpandedPyMISP, MISPEvent
import paramiko
import os
import json
import argparse

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


def main():
    """
    main
    """
    args = cli()
    logger, sftp_c, misp_c = init(args.config)
    key = paramiko.RSAKey.from_private_key_file(sftp_c["private_key_file"], sftp_c["private_key_password"])
    ssh = paramiko.SSHClient()
    ssh.load_host_keys(sftp_c["known_hosts_file"])
    ssh.connect(sftp_c["host"], port=sftp_c["port"], username=sftp_c["username"], pkey=key)
    event_added = 0
    event_updated = 0

    with ssh.open_sftp() as sftp:
        sftp.chdir(sftp_c["sftp_directory"])
        content = sftp.listdir_attr()
        misp = misp_init(misp_c)
        for file in content:
            if(file.filename.split('.')[-1] == "json"):
                local_file_name = sftp_c["local_directory"] + "/" + file.filename
                sftp.get(file.filename, local_file_name)
                event=MISPEvent()
                event.load_file(local_file_name)
                if event_already_exist(misp, event):
                    if not event_not_updated(misp, event):
                        misp.update_event(event, pythonify=True)
                        logger.info("Event %s updated", file.filename)
                        event_updated+=1
                    else:
                        logger.info("Event %s was not updated", file.filename)
                else:
                    misp.add_event(event, pythonify=True)
                    logger.info("Event %s added", file.filename)
                    event_added+=1
        logger.info("Total : %s events updated and %s events added", event_updated, event_added)




if __name__ == "__main__":
    # execute only if run as a script
    main()
