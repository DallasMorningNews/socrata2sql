# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]


## 0.1.3 - 2019-03-05

#### Fixed

- Fix the check for PostGIS extensions: when in postgres — but without these extensions created — the importer should no longer fail.
- Fix missing `-d` flag in docstring PostgreSQL example


## 0.1.2 - 2019-02-08

#### Fixed

- Fix `KeyError` during count queries in older versions of Socrata API ([#1](https://github.com/DallasMorningNews/socrata2sql/issues/1))


## 0.1.1 - 2019-02-07

#### Added
- README in Markdown format for PyPi
- this [change log](https://keepachangelog.com/en/1.0.0/)


## 0.1.0 - 2019-02-07

Initial release
