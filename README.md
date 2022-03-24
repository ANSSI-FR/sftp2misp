# :fr: sftp2misp

Script d'automatisation de la récupération de fichiers JSON MISP sur un serveur SFTP pour import par API sur une instance MISP.

## Pré-requis

- un serveur SFTP avec authentification par clé SSH
- une instance MISP (> 2.4.130) avec authentification par clé d'API (rôle Sync User)
- un serveur Linux disposant de python 3.8 pour l'exécution du script

## Installation

De préférence, faire usage d'un environnement virtuel (virtualenv) Python pour l'installation des dépendances :

- Création du virtualenv : `python3 -m venv path/to/venv`  
- Activation du virtualenv : `source path/to/venv/bin/activate`  
- Installation des dépendances : `pip install -r requirements.txt`  


## Configuration

Le fichier de configuration par défaut des variables d'environnement et des paramètres est `conf/config.yaml`.
- Copier le fichier de configuration modèle : `cp conf/config.template.yaml conf/config.yaml`
- Éditer `conf/config.yaml` en fonction de votre environnement, l'aide est fournie dans les commentaires.

Par défaut :
- le dossier de sauvegarde des fichiers JSON MISP téléchargés est `./misp-json`.
- le fichier de journalisation est `./log/sftp_log_datedujour.log`.

## Exécution

Si le virtualenv Python est activé : `python3 sftp2misp.py ` ou `path/to/venv/bin/python3 sftp2misp.py` sinon.

Options
  - `-c, --config CONFIG_FILE` pour spécifier un fichier de configuration `CONFIG_FILE` alternatif à `config/config.yaml`
  - `-n, --no-download` pour ne pas exécuter l'étape de téléchargement des fichiers JSON MISP, correspond à l'import des fichiers JSON MISP présents dans le sous-dossier `./misp-json`

Lors de la connexion au serveur SFTP, si votre clé privée à été générée avec un mot de passe, vous devrez le rentrer manuellement.

# :gb: :us: sftp2misp

Automation script to download JSON MISP files from a SFTP server and import them via API to a MISP instance.

## Requirements

- a SFTP server with SSH key-based authentication
- a MISP server (> 2.4.130) with API key-based authentication (Sync User role)
- a Linux server with python 3.8 to run the script 

## Installation

Preferably, use a Python virtual environment (virtualenv) Python to install dependencies :

- Create virtualenv : `python3 -m venv path/to/venv`  
- Activate virtualenv : `source path/to/venv/bin/activate`  
- Install dependencies : `pip install -r requirements.txt`  

## Configuration

Default configuration file for environment variables and parameters is `conf/config.yaml`.
- Copy configuration file template : `cp conf/config.template.yaml conf/config.yaml`
- Edit `conf/config.yaml` depending on your environment, help is available in comments.

By default :
- Download folder for JSON MISP files is `./misp-json`.
- Logging file is `./log/sftp_log_dateoftoday.log`.

## Run

If Python virtualenv is activated : `python3 sftp2misp.py ` otherwise `path/to/venv/bin/python3 sftp2misp.py`.

Options
  - `-c, --config CONFIG_FILE` to specify `CONFIG_FILE` as an alternative configuration file to `config/config.yaml`
  - `-n, --no-download` to bypass JSON MISP files download, and just import into MISP the JSON MISP files from subfolder `./misp-json`

When connecting to the SFTP server, if your private key has been generated with a password, you will need to enter it manually.
