import click
import logging
import pandas as pd
import requests
import sys

logger = logging.getLogger(__name__)


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
    logger.info("communes, quartiers and adresses have been retrieved")
    logger.info("We will now retrieve all the collect details without any multithreading")
    collectes = collect_to_df(list(cqa['adresse_id'].values))
    data = cqa.merge(collectes, on='adresse_id')
    data.to_csv(f'{output_file}', index=False)


@click.command()
@click.option('--debug', is_flag=True, help="Turn on debug logging")
@click.option('--output', default="data/cacem-dechets-old.csv", help="output csv location")
def main(debug: bool, output: str):
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=level)

    logger.info("Retrieving data started. We are (very) nice, so please be (very) patient")
    get_data(output)


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
