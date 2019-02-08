"""Socrata to SQL database loader

Load a dataset from a Socrata-powered open data portal into a SQL database.
Uses the Socrata API to inspect the dataset, then sets up a table with matching
SQL types and loads all rows. The loader supports any database supported by
SQLalchemy.

Usage:
  socrata2sql insert <site> <dataset_id> [-d=<database_url>] [-a=<app_token>] [-t=<table_name>]
  socrata2sql ls <site> [-a=<app_token>]
  socrata2sql (-h | --help)
  socrata2sql (-v | --version)

Options:
  <site>             The domain for the open data site. Ex: www.dallasopendata.com
  <dataset_id>       The ID of the dataset on the open data site. This is usually
                     a few characters, separated by a hyphen, at the end of the
                     URL. Ex: 64pp-jeba
  -d=<database_url>  Database connection string for destination database as
                     dialect+driver://username:password@host:port/database.
                     Default: sqlite:///<dataset name>.sqlite
  -t=<table_name>    Destiation table in the database. Defaults to a sanitized
                     version of the dataset's name on Socrata.
  -a=<app_token>     App token for the site. Only necessary for high-volume
                     requests. Default: None
  -h --help          Show this screen.
  -v --version       Show version.

Examples:
  List all datasets on the Dallas open data portal:
  $ socrata2sql ls www.dallasopendata.com

  Load the Dallas check register into a local SQLite file (file name chosen
  from the dataset name):
  $ socrata2sql insert www.dallasopendata.com 64pp-jeba

  Load it into a PostgreSQL database call mydb:
  $ socrata2sql insert www.dallasopendata.com 64pp-jeba postgresql:///mydb
"""
from os import path
import re

from docopt import docopt
from geoalchemy2.types import Geometry
from progress.bar import FillingCirclesBar
from sodapy import Socrata
from sqlalchemy import Column
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.types import Boolean
from sqlalchemy.types import DateTime
from sqlalchemy.types import Integer
from sqlalchemy.types import Numeric
from sqlalchemy.types import Text
from tabulate import tabulate

from socrata2sql import __version__
from socrata2sql.exceptions import CLIError
from socrata2sql.parsers import parse_datetime
from socrata2sql.parsers import parse_geom
from socrata2sql.parsers import parse_str
from socrata2sql import ui


def get_sql_col(col_data_type):
    """Map a Socrata column type to a SQLalchemy column class"""
    col_mappings = {
        'checkbox': Boolean,
        'url': Text,
        'text': Text,
        'number': Numeric,
        'calendar_date': DateTime,
        'point': Geometry(geometry_type='POINT', srid=4326),
        'location': Geometry(geometry_type='POINT', srid=4326),
    }

    try:
        return Column(col_mappings[col_data_type])
    except KeyError:
        msg = 'Unable to map Socrata type "%s" to a SQL type.' % col_data_type
        raise NotImplementedError(msg)


def get_table_name(raw_str):
    """Transform a string into a suitable table name

    Swaps spaces for _s, lowercaes and strips special characters. Ex:
    'Calls to 9-1-1' becomes 'calls_to_911'
    """
    no_spaces = raw_str.replace(' ', '_')
    return re.sub(r'\W',  '', no_spaces).lower()


def default_db_str(dataset_metadata):
    """Create connection string to a local SQLite database from dataset name"""
    dataset_slug = get_table_name(dataset_metadata['name'])
    db_filename = '%s.sqlite' % dataset_slug

    if path.isfile(db_filename):
        msg_tpl = (
            '%s already exists. Specify a unique database name with -d. '
            'Example: -d sqlite:///unique_name.sqlite'
        )
        raise CLIError(msg_tpl % db_filename)

    return 'sqlite:///%s' % db_filename


def get_binding(socrata_client, dataset_id, dataset_metadata, geo, dest):
    if dest is None:
        table_name = get_table_name(dataset_metadata['name'])
    else:
        table_name = dest

    record_fields = {
        '__tablename__': table_name,
        '_pk_': Column(Integer, primary_key=True)
    }

    ui.header(
        'Setting up new table, "%s", from Socrata API fields' % table_name
    )

    for col in dataset_metadata['columns']:
        col_name = col['fieldName']
        col_type = col['dataTypeName']

        if col_type in ('location', 'point',) and geo is False:
            msg = (
                '"%s" is a %s column but your database doesn\'t support '
                'PostGIS so it\'ll be skipped.'
            ) % (col_name, col_type,)
            ui.item(msg)
            continue

        if col_name.startswith(':@computed'):
            ui.item('Ignoring computed column "%s".' % col_name)
            continue

        try:
            record_fields[col_name] = get_sql_col(col_type)
        except NotImplementedError as e:
            ui.item('%s' % str(e))
            continue

    return type('SocrataRecord', (declarative_base(),), record_fields)


def get_connection(db_str, dataset_metadata):
    if db_str is not None:
        engine = create_engine(db_str)
        ui.header('Connecting to database')
    else:
        default = default_db_str(dataset_metadata)
        ui.header('Connecting to database')
        engine = create_engine(default)
        ui.item('Using default SQLite database "%s".' % default)

    Session = sessionmaker()
    Session.configure(bind=engine)

    session = Session()

    # Check for PostGIS support
    gis_q = 'SELECT PostGIS_version();'
    try:
        session.execute(gis_q)
        geo_enabled = True
    except OperationalError:
        geo_enabled = False
    finally:
        session.commit()

    if geo_enabled:
        ui.item(
            'PostGIS is installed. Geometries on Socrata will be imported '
            'as PostGIS geoms.'
        )
    else:
        ui.item('Query "%s" failed. Geometry columns will be skipped.' % gis_q)

    return engine, session, geo_enabled


def get_row_count(socrata_client, dataset_id):
    """Get the row count of a Socrata dataset"""
    count = socrata_client.get(
        dataset_id,
        select='COUNT(*) AS count'
    )
    return int(count[0]['count'])


def get_dataset(socrata_client, dataset_id, page_size=5000):
    """Iterate over a datasets pages using the Socrata API"""
    page_num = 0
    more_pages = True

    while more_pages:
        api_data = socrata_client.get(
            dataset_id,
            limit=page_size,
            offset=page_size * page_num,
        )

        if len(api_data) < page_size:
            more_pages = False

        page_num += 1
        yield api_data


def list_datasets(socrata_client):
    """List all datasets on a portal using the Socrata API"""
    all_metadata = socrata_client.datasets()

    key_fields = []
    for dataset in all_metadata:
        if dataset['resource']['type'] != 'dataset':
            # Skip everything that isn't an original dataset
            continue

        # Simplify the metadata returned by the API
        key_fields.append({
            'Name': dataset['resource']['name'],
            'Category': dataset['classification'].get('domain_category'),
            'ID': dataset['resource']['id'],
            'URL': dataset['permalink']
        })

    return sorted(key_fields, key=lambda _: _['Name'].lower())


def parse_row(row, binding):
    """Parse API data into the Python types our binding expects"""
    parsers = {
        # This maps SQLAlchemy types (key) to functions that return their
        # expected Python type from the raw Socrata data.
        DateTime: parse_datetime,
        Geometry: parse_geom,
        Text: parse_str,
    }

    parsed = {}
    for col_name, col_val in row.items():
        binding_columns = binding.__mapper__.columns

        if col_name not in binding_columns:
            # We skipped this column when creating the binding; skip it now too
            continue

        mapper_col_type = type(binding_columns[col_name].type)

        if mapper_col_type in parsers:
            parsed[col_name] = parsers[mapper_col_type](col_val)
        else:
            parsed[col_name] = col_val

    return parsed


def main():
    arguments = docopt(__doc__, version=__version__)

    client = Socrata(arguments['<site>'], arguments['-a'])

    try:
        if arguments['ls']:
            datasets = list_datasets(client)
            print(tabulate(datasets, headers='keys', tablefmt='psql'))
        elif arguments['insert']:
            dataset_id = arguments['<dataset_id>']
            metadata = client.get_metadata(dataset_id)

            engine, session, geo = get_connection(arguments['-d'], metadata)
            Binding = get_binding(
                client, dataset_id, metadata, geo, arguments['-t']
            )

            try:
                Binding.__table__.create(engine)
            except ProgrammingError as e:
                if 'already exists' in str(e):
                    raise CLIError(
                        'Destination table already exists. Specify a new table'
                        ' name with -t.'
                    )
                raise CLIError('Error creating destination table: %s' % str(e))

            num_rows = get_row_count(client, dataset_id)
            bar = FillingCirclesBar('  ▶ Loading from API', max=num_rows)

            for page in get_dataset(client, dataset_id):
                to_insert = []
                for row in page:
                    to_insert.append(Binding(**parse_row(row, Binding)))

                session.add_all(to_insert)
                bar.next(n=len(to_insert))

            bar.finish()

            ui.item(
                'Committing rows (this can take a bit for large datasets).'
            )
            session.commit()

            success = 'Successfully imported %s rows from "%s".' % (
                num_rows, metadata['name']
            )
            ui.header(success, color='\033[92m')

        client.close()
    except CLIError as e:
        ui.header(str(e), color='\033[91m')


if __name__ == '__main__':
    main()
