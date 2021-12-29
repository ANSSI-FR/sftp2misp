# Sigpart Pull

Script d'automatisation du pull est events sigpart : SFTP -> MISP des bénéficiaires, pour simplifier le partage.

## Installation

De préférence faire usage d'un virtualenv python :
Creation du virtualenv : `python3 -m venv path/to/venv`  
Activation du virtual env : `source path/to/venv/bin/activate`  
Installation des dependences : `pip install -r requirements.txt`  

## Configuration
`cp conf/config.template.yaml conf/config.yaml`  
puis éditer `conf/conf.yaml` en fonction de votre environnement

Le dossier par défaut de sauvegarde des events est ./output et le fichier de sauvegarde des logs par défaut est ./log/sftp.log.

## Lancement du programme
`python3 sftp2misp.py `  



Options
  - -c configfile -> Fournir un fichier de configuration avec un nom différent dde config.yaml
