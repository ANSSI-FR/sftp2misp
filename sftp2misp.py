import config
from pymisp import ExpandedPyMISP, MISPEvent
import os
import argparse

import subprocess
import sys

def init(config_file):
    """
    Initialise les dossiers locaux et la paramètres selon la
    configuration.
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
    Initialise la connexion à l'instance MISP en instanciant un objet
    ExpandedPyMISP avec les bons paramètres.
    """
    config.set_ssl(misp_c)
    return ExpandedPyMISP(misp_c["url"],
                          misp_c["key"],
                          misp_c["ssl"])


def cli():
    """
    Initialise les arguments du scripts.
    """
    parser = argparse.ArgumentParser(description='Transfer event from sftp to misp')
    parser.add_argument("-c", "--config",
                        required=False, default="./conf/config.yaml",
                        help="Fichier de configuration différent de config.yaml")
    return parser.parse_args()


def event_already_exist(misp, event) -> bool:
    """
    Test si l'évenements en cours  de traitement existe déja dans l'instance
    MISP.
    """
    event_uuid = event.get("uuid")
    return misp.event_exists(event_uuid)


def event_not_updated(misp, local_event) -> bool:
    """
    Test si l'évenements en cours de traitement à été mis à jour par rapport
    à la version actuelle dans l'instance MISP.
    """
    local_event_uuid = local_event.get("uuid")
    local_event_timestamp = local_event.get("timestamp")
    misp_event = misp.get_event(local_event_uuid, pythonify=True)
    misp_event_timestamp = misp_event.get("timestamp")
    return local_event_timestamp == misp_event_timestamp


def event_deleted(misp, event) -> bool:
    """
    Test si l'évenements en cours de traitement à été précédemment supprimé
    de l'instance MISP.
    """
    blocklist = misp.event_blocklists()
    event_uuid = event.get("uuid")
    for ev in blocklist:
        if ev.get("event_uuid") == event_uuid:
            return True
    return False


def get_events(identity_file,
               proxy_command,
               host_ip,
               port,
               user,
               server_dir,
               local_dir):
    """
    Récupère la liste des évenements disponibles sur l'instance FTP.
    """
    subprocess.run(["sftp",
                    "-i", f"{identity_file}",
                    f"-o ProxyCommand={proxy_command}",
                    "-P", f"{port}",
                    f"{user}@{host_ip}:{server_dir}/*.json {local_dir}"], check=True)


def upload_events(misp, local_dir, logger):
    """
    Pour chaque events dans le dossier local_dir, instancie un MISPEvent et
    tente de l'ajouter à l'instance MISP.
    """
    _event_updated = 0
    _event_not_updated = 0
    _event_added = 0
    _event_deleted = 0
    for filename in os.listdir(local_dir):
        file = os.path.join(local_dir, filename)
        event = MISPEvent()
        event.load_file(file)
        if event_already_exist(misp, event):
            if not event_not_updated(misp, event):
                misp.update_event(event, pythonify=False)
                logger.info("Event %s mis à jour", file)
                _event_updated += 1
            else:
                _event_not_updated += 1
                logger.info("Event %s existant et non mis à jour", file)
        elif event_deleted(misp, event):
            _event_deleted += 1
            logger.info("Event %s supprimé, dans la blocklist", file)
        else:
            misp.add_event(event, pythonify=False)
            logger.info("Event %s ajouté", file)
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
    #get_events(sftp_c["private_key_file"],
    #           sftp_c["proxy_command"],
    #           sftp_c["host"], sftp_c["port"], sftp_c["username"],
    #           sftp_c["sftp_directory"], sftp_c["local_directory"])
    upload_events(misp, sftp_c["local_directory"], logger)

if __name__ == "__main__":
    # execute only if run as a script
    main()
