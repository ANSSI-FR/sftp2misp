# :fr: sftp2misp

Script d'automatisation de la récupération de fichiers JSON MISP sur un serveur SFTP pour import par API sur une instance MISP.

## Pré-requis

- un serveur SFTP avec authentification par clé SSH
- une instance MISP (> 2.4.130) avec authentification par clé d'API (rôle Sync User)
- un serveur Linux disposant de python 3.8 pour l'exécution du script

## Installation

De préférence, faire usage d'un environnement virtuel (virtualenv) Python pour l'installation des dépendances.

Pour une installation automatisée, exécuter `make init` à la racine du répertoire projet.

Pour une installation pas à pas :
- Création du virtualenv : `python3 -m venv path/to/venv`  
- Activation du virtualenv : `source path/to/venv/bin/activate`  
- Installation des dépendances : `pip install -r requirements.txt`  


## Configuration

Le fichier de configuration par défaut des variables d'environnement et des paramètres est `conf/config.yaml`.
- Copier le fichier de configuration modèle : `cp conf/config.yaml.template conf/config.yaml`.
- Éditer `conf/config.yaml` en fonction de votre environnement, l'aide est fournie dans les commentaires.

Par défaut :
- le dossier de sauvegarde des fichiers JSON MISP téléchargés est `./json_misp` ;
- le fichier de journalisation est `./log/YYYYMMDD_sftp2misp.log`.

La journalisation est configurable dans le fichier `conf/logging.yaml`:  
- L'option `level` de `console` et `file` permet de choisir le filtre d'affichage de la journalisation, respectivement dans la console et dans les fichiers de journalisation. Les options sont `DEBUG`, `INFO` (par défaut), `WARNING` et `ERROR` à paramètrer selon vos besoins.

## Exécution

Si le virtualenv Python est activé : `python3 sftp2misp.py ` ou `path/to/venv/bin/python3 sftp2misp.py` sinon.

Options
  - `-h, --help` pour obtenir de l'aide
  - `-c CONFIG, --config CONFIG` pour spécifier un fichier de configuration `CONFIG` alternatif à `config/config.yaml`
  - `-n, --no-download` pour ne pas exécuter l'étape de téléchargement des fichiers JSON MISP, correspond à l'import des fichiers JSON MISP dans MISP
  - `-d, --delete-local-directory-content` pour effacer le contenu du répertoire `local_directory` avant le téléchargement des fichiers JSON MISP
  - `-q, --quiet` pour réduire à une occurrence chaque message d'avertissement dans les ficheirs de journalisation
  - `-v, --verbose` pour activer le mode verbose du logger et afficher les messages de debug

Lors de la connexion au serveur SFTP, si votre clé privée est protégée par un mot de passe, vous devrez le saisir manuellement.

# :gb: :us: sftp2misp

Automation script to download JSON MISP files from a SFTP server and import them via API to a MISP instance.

## Requirements

- a SFTP server with SSH key-based authentication
- a MISP server (> 2.4.130) with API key-based authentication (Sync User role)
- a Linux server with python 3.8 to run the script

## Installation

Preferably, use a Python virtual environment (virtualenv) to install dependencies.

For automated installation, run `make init` in project root directory.

For a step by step installation :
- Create virtualenv : `python3 -m venv path/to/venv`  
- Activate virtualenv : `source path/to/venv/bin/activate`  
- Install dependencies : `pip install -r requirements.txt`  

## Configuration

Default configuration file for environment variables and parameters is `conf/config.yaml`.
- Copy configuration file template : `cp conf/config.yaml.template conf/config.yaml`.
- Edit `conf/config.yaml` depending on your environment, help is available in comments.

By default :
- Download folder for JSON MISP files is `./json_misp`.
- Logging file is `./log/YYYYMMDD_sftp2misp.log`.

Logging is configurable in file `conf/logging.yaml`:  
- Option `level` in `console` and `file` allows to choose the logging filter, respectively in terminal and in logging files. Options are `DEBUG`, `INFO` (default), `WARNING` and `ERROR` to be set according to your needs.

## Run

If Python virtualenv is activated : `python3 sftp2misp.py ` otherwise `path/to/venv/bin/python3 sftp2misp.py`.

Options
  - `-h, --help` to get help
  - `-c CONFIG, --config CONFIG` Specify `CONFIG` as an alternative configuration file to `./conf/config.yaml`
  - `-n, --no-download ` Bypass JSON MISP files download, and just import the local JSON MISP files into MISP instance
  - `-d, --delete-local-directory-content` Erase the content of the `local_directory` before JSON MISP files are downloaded
  - `-q, --quiet` Reduce spam in logs by showing warnings only once
  - `-v, --verbose` to activate logger verbose mode and show debug messages

When connecting to the SFTP server, if your private key is protected by a password, you shall enter it manually.
