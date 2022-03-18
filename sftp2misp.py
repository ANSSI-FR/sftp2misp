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
    parser = argparse.ArgumentParser(description='Transferer des events d\'un \
                                                  serveur sftp vers une instance misp')
    parser.add_argument("-c", "--config",
                        required=False, default="./conf/config.yaml",
                        help="Fichier de configuration différent de config.yaml")
    parser.add_argument("-n", "--no-download",
                        action='store_true',
                        help="Si spécifiée, effectue uniquement l'insertion dans misp")
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


def get_events(identity_file,
               proxy_command,
               host_ip,
               port,
               user,
               server_dir,
               local_dir, logger):
    """
    Récupère la liste des évenements disponibles sur l'instance FTP.
    """
    old_file_number = len([name for name in os.listdir(local_dir) if os.path.isfile(os.path.join(local_dir, name))])
    subprocess.run(["sftp",
                    "-i", f"{identity_file}",
                    f"-o ProxyCommand={proxy_command}",
                    "-P", f"{port}",
                    f"{user}@{host_ip}:{server_dir}/*.json {local_dir}"], check=True)
    new_file_number = len([name for name in os.listdir(local_dir) if os.path.isfile(os.path.join(local_dir, name))])
    logger.info(f"{new_file_number-old_file_number} events téléchargés")


def upload_events(misp, local_dir, logger):
    """
    Pour chaque events dans le dossier local_dir, instancie un MISPEvent et
    tente de l'ajouter à l'instance MISP.
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
                logger.info(f"Event {file} mis à jour")
                _event_updated += 1
            else:
                _event_not_updated += 1
                logger.info(f"Event {file} existant et non mis à jour")
        else:
            rep = misp.add_event(event, pythonify=False)
            if "errors" in rep:
                logger.warning(f"Erreur sur l'event : {file}")
                logger.warning(rep)
                if rep["errors"][1]["name"] == "Event blocked by event blocklist.":
                    _event_deleted += 1
                else :
                    _event_error += 1
            else:
                logger.info(f"Event {file} ajouté")
                _event_added += 1
    logger.info(f"Total : \
                \n\t {_event_updated} events mis à jour \
                \n\t {_event_added} events ajoutés \
                \n\t {_event_deleted} events non ajoutés car dans la blocklist (supprimé précédemment) \
                \n\t {_event_not_updated} events non mis à jour \
                \n\t {_event_error} erreurs d'importation")


def main():
    """
    main
    """
    args = cli()
    logger, sftp_c, misp_c = init(args.config)
    misp = misp_init(misp_c)
    if not args.no_download:
        get_events(sftp_c["private_key_file"],
                  sftp_c["proxy_command"],
                  sftp_c["host"], sftp_c["port"], sftp_c["username"],
                  sftp_c["sftp_directory"], sftp_c["local_directory"], logger)
    upload_events(misp, sftp_c["local_directory"], logger)

if __name__ == "__main__":
    # execute only if run as a script
    main()
