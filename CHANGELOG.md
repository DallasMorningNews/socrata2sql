# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

#### Fixed
- Fix missing `-d` flag in docstring PostgreSQL example
- Pass domain to Socrata API when using `ls`, since the Socrata API no longer filters by domain on its own ([#4](https://github.com/DallasMorningNews/socrata2sql/pull/4))

#### Added
- Adds a very basic first effort at tests ([#4](https://github.com/DallasMorningNews/socrata2sql/pull/4))

#### Changed
- The `ls` command originally filtered out non-datasets locally; now that's done at the API level ([#4](https://github.com/DallasMorningNews/socrata2sql/pull/4))

## 0.1.2 - 2019-02-08

#### Fixed

- Fix `KeyError` during count queries in older versions of Socrata API ([#1](https://github.com/DallasMorningNews/socrata2sql/issues/1))

## 0.1.1 - 2019-02-07

#### Added
- README in Markdown format for PyPi
- this [change log](https://keepachangelog.com/en/1.0.0/)

## 0.1.0 - 2019-02-07

Initial release
