import yaml
import logging, logging.config
import os

def get_config():
    with open("conf/config.yaml", "r") as config_file:
        return yaml.safe_load(config_file)

config = get_config()
sftp_c=config["SFTP"]
misp_c=config["MISP"]
misc_c=config["MISC"]

def get_logging_config():
    with open(misc_c["logging_conf"], "r") as config_file:
        return yaml.safe_load(config_file)
def get_logger():
    try:
        os.mkdir("./log")
    except FileExistsError:
        pass
    except:
        print("Unexpected error: ", sys.exc_info()[0])
        raise
    logging.config.dictConfig(get_logging_config()["LOGGING"])
    return logging.getLogger(__name__)

if(misp_c["ssl"]):
    os.environ['REQUESTS_CA_BUNDLE'] = CONFIG["MISP_CONF"]["CA_BUNDLE"]

logger = get_logger()
logger.info('Chargement du fichier de configuration terminé')
