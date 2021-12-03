from config import sftp_c, misp_c, logger
from pymisp import ExpandedPyMISP, MISPEvent
import pysftp
import os
import json

def init():
    """
    init local directory to download event files from ftp server
    """
    try:
        os.mkdir(sftp_c["local_directory"])
    except FileExistsError:
        pass
    except:
        logger.info("Unexpected error: %s", sys.exc_info()[0])
        raise


def misp_init():
    """
    init connexion to misp instance
    """
    return ExpandedPyMISP(misp_c["url"],
                          misp_c["key"],
                          misp_c["ssl"])


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
    init()
    event_added = 0
    event_updated = 0
    with pysftp.Connection(host=sftp_c["host"],
                           username=sftp_c["username"],
                           password=sftp_c["password"]) as sftp:
        sftp.cwd(sftp_c["sftp_directory"])
        content = sftp.listdir_attr()
        misp = misp_init()
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
                    logger.info("Event %s add", file.filename)
                    event_add+=1
        logger.info("Total : %s events updated and %s events added", event_updated, event_added)




if __name__ == "__main__":
    # execute only if run as a script
    main()
