# 🏛️ socrata2sql ![](https://img.shields.io/pypi/v/socrata2sql.svg?style=flat) ![LICENSE](https://img.shields.io/github/license/DallasMorningNews/socrata2sql.svg?style=flat)

Plenty of state and local governments use Socrata to run their open data portals. This tool allows you to grab a dataset from one of these portals and copy it into a SQL database of your choice. It uses the Socrata API to understand the columns in the dataset and attempts to create correctly-typed columns in the SQL database to match, including PostGIS geometries if the database and source dataset support them.

## Requirements

- Python 3.x

## Installation

```sh
$ pipenv install socrata2sql
```

*or*

```sh
$ pip install socrata2sql
```

## Usage

```
Socrata to SQL database loader

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
```

## Copyright

&copy; 2019 The Dallas Morning News
