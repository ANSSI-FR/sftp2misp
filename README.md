# Sigpart Pull

Script d'automatisation du pull est events sigpart : SFTP -> MISP des bénéficiaires, pour simplifier le partage.


create a virtual env : ```python3 -m venv path/to/venv```   
activate virtual env : source path/to/venv/bin/activate  
install dependencies : pip install -r requirements.txt  
   
cp conf/conf.template.yaml conf/conf.yaml  
edit conf/conf.yaml to your environnment  

python3 sftp2misp.py   
  
[options : -c configfile]
