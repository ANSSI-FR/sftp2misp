# :fr: sftp2misp

Script d'automatisation de la récupération de fichiers JSON MISP sur un serveur SFTP pour import par API sur une instance MISP.

## Pré-requis

- un serveur SFTP avec authentification par clé SSH
- une instance MISP (> 2.4.150) avec authentification par clé d'API (rôle Sync User)
- un serveur Linux disposant de python 3.8 pour l'exécution du script

## Installation

De préférence, faire usage d'un environnement virtuel (virtualenv) Python pour l'installation des dépendances :

- Création du virtualenv : `python3 -m venv path/to/venv`  
- Activation du virtualenv : `source path/to/venv/bin/activate`  
- Installation des dépendances : `pip install -r requirements.txt`  

## Configuration

Le fichier de configuration des variables d'environnement et des paramètres est `conf/config.yaml`.
- Copier le fichier de configuration modèle : `cp conf/config.template.yaml conf/config.yaml`
- Éditer `conf/config.yaml` en fonction de votre environnement, l'aide est fournie dans les commentaires.

Par défaut :
- le dossier de sauvegarde des fichiers JSON MISP téléchargés est `./output`.
- le fichier de journalisation est `./log/sftp.log`.

## Exécution

Si le virtualenv Python est activé : `python3 sftp2misp.py ` ou `path/to/venv/bin/python3 sftp2misp.py` sinon.

Options
  - `-c configfile` pour spécifier un fichier de configuration alternatif à `config/config.yaml`
  - (à venir) `--no-download` pour ne pas exécuter l'étape de téléchargement des fichiers JSON MISP, correspond à l'import des fichiers JSON MISP présents dans le sous-dossier `./output`

# :gb: :us: sftp2misp

Automation script to download JSON MISP files from a SFTP server and import them via API to a MISP instance.

## Requirements

## Installation

## Configuration

## Run
