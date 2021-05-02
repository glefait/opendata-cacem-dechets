import click
import logging
import numpy as np
import os
import pandas as pd
import requests
import sys

logger = logging.getLogger(__name__)
CSV_FILE = 'data/cacem-dechets.csv'
ANALYSE_DIR = 'data/analyse'


def requests_retry_session(retries=10, backoff_factor=0.5, status_forcelist=(500, 502, 504), session=None):
    session = session or requests.Session()
    retry = requests.packages.urllib3.util.retry.Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = requests.adapters.HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    return session


def collect_to_df(collecte_ids):
    data = []
    s = requests.Session()
    for collecte_id in collecte_ids:
        r = requests_retry_session(session=s).get(f'https://collecte-dechets.cacem.fr/get/collectes/{collecte_id}')
        data_json = r.json()
        data += [
            [
                data_json['adresse']['id'],
                collecte['title'],
                day,
                collecte['week_type']
            ]
            for collecte in data_json['collectes'] for day in collecte['days']
        ]
    df = pd.DataFrame(data, columns=['adresse_id', 'type_collecte', 'jour', 'type_semaine'])
    return df


def get_data(output_file):
    communes = (pd.read_json('https://collecte-dechets.cacem.fr/get/communes', orient='record')
                  .rename(columns={'id': 'commune_id', 'name': 'commune_name'}))
    quartiers = (pd.read_json('https://collecte-dechets.cacem.fr/get/quartiers', orient='record')
                   .rename(columns={'id': 'quartier_id', 'name': 'quartier_name'}))
    adresses = (pd.read_json('https://collecte-dechets.cacem.fr/get/adresses', orient='record')
                  .rename(columns={'id': 'adresse_id', 'name': 'adresse_name'}))
    cqa = communes.merge(quartiers, on="commune_id").merge(adresses, on="quartier_id")
    logger.info('communes, quartiers and adresses have been retrieved')
    logger.info('We will now retrieve all the collect details without any multithreading')
    collectes = collect_to_df(list(cqa['adresse_id'].values))
    data = cqa.merge(collectes, on='adresse_id')
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    data.to_csv(f'{output_file}', index=False)
    logger.info(f'csv written to {output_file}')


@click.group()
@click.option('--debug', is_flag=True, help="Turn on debug logging, if any")
@click.pass_context
def main(ctx, debug: bool):
    ctx.ensure_object(dict)
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=level)
    ctx.obj['DEBUG'] = debug


@main.command()
@click.option('--output', default=CSV_FILE, help='downloaded output csv path')
@click.pass_context
def get(ctx, output):
    logger.info('Retrieving data started. We are (very) nice, so please be (very) patient')
    get_data(output)


@main.command()
@click.option('--output_dir', default=ANALYSE_DIR, help='directory to write analysis')
@click.pass_context
def analyse(ctx, output_dir):
    print("analyse")
    # check that CSV_FILE exists
    df = pd.read_csv(CSV_FILE)
    df['freq'] = np.where(df['type_semaine'].isnull(), 1, 0.5)
    # 1. Recherche les adresses pour lesquelles il manque l'information d'un type de collecte.
    df_cat = (df[['adresse_id', 'type_collecte', 'freq']]
              .groupby(['adresse_id', 'type_collecte'])
              .agg('sum')
              .reset_index()
              .pivot(index='adresse_id', columns='type_collecte', values='freq')
              .fillna(0))
    agg = (df[['commune_id', 'commune_name', 'quartier_id', 'quartier_name', 'adresse_id', 'adresse_name']]
           .groupby(by='adresse_id')
           .first()
           .reset_index()
           .merge(df_cat, on='adresse_id'))
    # adresse_id sans collecte définie
    collectes_manquantes_list = []
    for collecte in df['type_collecte'].unique():
        sub = agg[agg[collecte] == 0][['commune_name', 'quartier_name', 'adresse_name', 'adresse_id']]
        sub['collecte_manquante'] = collecte
        collectes_manquantes_list.append(sub)
    collectes_manquantes = pd.concat(collectes_manquantes_list)
    os.makedirs(ANALYSE_DIR, exist_ok=True)
    collectes_manquantes.to_csv(os.path.join(ANALYSE_DIR, 'collectes-manquantes.csv'), index=False)


if __name__ == '__main__':
    sys.exit(main(obj={}))  # pragma: no cover
