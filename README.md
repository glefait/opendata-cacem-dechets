# opendata-cacem-dechets

Génération d'un fichier CSV reprennant les données de [ramassage de déchets](https://collecte-dechets.cacem.fr/).

Ce projet est:
- volontairement overkill. Le packaging python et l'image docker sont pour l'exemple. Un script de 50 lignes aurait suffit.
- abusivement nice avec l'infrastructure distante = pas de multi-threading.
- gère un minimum d'erreur réseau puisque je suis chez SFR Caraibes.

## Rappel
La mise à disposition des données "par principe" est une [obligation légale](https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000033202746/) pour les collectivités de plus de 3500 habitants depuis 2018.
La Cacem, avec ses [158.944 habitants](http://www.cacem.fr/lagglo/histoire-competences.html), est donc soumise à cette obligation légale.

# Problèmes identifiés

1. Ramassage non définie
Le fichier [data/analyse/collectes-manquantes.csv](data/analyse/collectes-manquantes.csv) présente les adresses pour lesquelles au moins un type de ramassage n'est pas définie.

# Todo
- [ ] vérifier avec la Cacem si les problèmes d'intégrité des données sont réels
- [ ] vérifier que faire du multithreading ne va pas détruire l'infra Cacem
- [ ] ajouter une entrée sur [data.gouv.fr](http://data.gouv.fr/)
- [ ] Réutiliser les données pour faire un système d'alerte et de remontée des "non-passages".

# Run and build

## python

Unless you really know what you are doing, run it on a virtualenv.

If you have no idea of what you are doing, just use docker or docker-compose.

### Install

    mkvirtualenv opendata-cacem-dechets
    pip install . -r requirements.txt

### Run

    opendata-cacem-dechets

Output csv file can be configured with

    opendata_cacem_dechets  --output /tmp/opendata-cacem-dechet.csv

## docker

    docker run --rm -v $PWD/data:/open/data -it $(docker build -q .)

If you need to rebuild the container, add the `--no-cache` option:

    docker run --rm -v $PWD/data:/open/data -it $(docker build --no-cache -q .)

### Change the parameter
To start the analysis, you just need to change the `CMD` parameter, as shown below:

    docker run --rm -v $PWD/data:/open/data -it $(docker build --no-cache -q .) "analyse"

## docker-compose

    docker-compose up

### to rebuild

    docker-compose up --build --force-recreate

### to clean

    docker-compose down -v

# Changelog
## 2021-05-02: init
