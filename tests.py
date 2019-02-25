#! /usr/bin/env python
from datetime import datetime
import unittest
from unittest.mock import patch

from socrata2sql.cli import get_table_name
from socrata2sql.parsers import parse_datetime
from socrata2sql.parsers import parse_geom
from socrata2sql.parsers import parse_str
from socrata2sql import ui


class DateTimeParserTestCase(unittest.TestCase):
    """Tests for parser for Socrata floating timestamp fields"""
    def test_empty(self):
        """Should return None if the raw value is blank"""
        self.assertIsNone(parse_datetime(''))

    def test_old_api_fmt(self):
        """Should parse timestamps for pre-Socrata API 2.1 to datetimes"""
        self.assertEqual(
            parse_datetime('2014-10-13T10:05:00'),
            datetime(2014, 10, 13, 10, 5)
        )

    def test_new_api_fmt(self):
        """Should parse ISO-8601 timestamps for Socrata API 2.1 to datetimes"""
        self.assertEqual(
            parse_datetime('2014-10-13T10:05:00.000'),
            datetime(2014, 10, 13, 10, 5)
        )


class GeomParserTestCase(unittest.TestCase):
    """Tests for parser for Socrata Location and Point fields"""
    def test_null(self):
        """Should return null values untouched"""
        self.assertIsNone(parse_geom(None))

    def test_location_point(self):
        """Should return locations that contain lat long as EWKT points"""
        self.assertEqual(parse_geom(
            {'longitude': -87.761102, 'latitude': 41.8657001},
        ), 'SRID=4326;POINT(41.8657001 -87.761102)')

    def test_location_no_lat_lng(self):
        """Should return locations without coordinates as nulls"""
        self.assertIsNone(parse_geom({'human_address': '100 Main St'}))

    def test_point(self):
        """Should return Points as EWKT point strings"""
        self.assertEqual(parse_geom(
            {'type': 'Point', 'coordinates': [41.8657001, -87.761102]}
        ), 'SRID=4326;POINT(41.8657001 -87.761102)')

    def test_unrecognized(self):
        """Should raise an error for unrecognized location formats"""
        with self.assertRaises(NotImplementedError):
            parse_geom({'type': 'Circle'})


class StrParserTestCase(unittest.TestCase):
    def test_url(self):
        """Should Socrata URL datatype (now deprecated)"""
        self.assertEqual(
            parse_str({'url': 'http://a.co'}),
            'http://a.co'
        )

    def test_dict(self):
        """Should serialize complex datatypes to JSON"""
        self.assertEqual(
            parse_str({'x': 'y'}),
            '{"x": "y"}'
        )

    def test_str(self):
        """Should return strings untouched"""
        self.assertEqual(parse_str('x'), 'x')


@patch('socrata2sql.ui.print')
class UiTestCase(unittest.TestCase):
    """Tests for the console ouptut functions"""
    def test_header(self, patched_print):
        """Should print a bold string to the console with the passed color"""
        ui.header('header', color='\033[91m')
        patched_print.assert_called_once_with('\n\033[1m\033[91mheader\033[0m')

    def test_item(self, patched_print):
        """Should print the passed item prefixed with a unicode caret"""
        ui.item('item')
        patched_print.assert_called_once_with('  ▶ item')


class DbTestCase(unittest.TestCase):
    def test_get_table_name(self):
        self.assertEqual(get_table_name('Calls to 9-1-1'), 'calls_to_911')


if __name__ == '__main__':
    unittest.main()
