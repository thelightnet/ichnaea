from ichnaea.db import (
    Cell,
    Wifi,
)
from ichnaea.tests.base import AppTestCase


class TestSearch(AppTestCase):

    def test_ok_cell(self):
        app = self.app
        session = self.db_slave_session
        cell = Cell()
        cell.lat = 123456781
        cell.lon = 234567892
        cell.radio = 2
        cell.mcc = 123
        cell.mnc = 1
        cell.lac = 2
        cell.cid = 1234
        session.add(cell)
        session.commit()

        res = app.post_json('/v1/search',
                            {"radio": "gsm",
                             "cell": [{"radio": "umts", "mcc": 123, "mnc": 1,
                                       "lac": 2, "cid": 1234}]},
                            status=200)
        self.assertEqual(res.content_type, 'application/json')
        self.assertEqual(res.body, '{"status": "ok", "lat": 12.3456781, '
                                   '"lon": 23.4567892, "accuracy": 35000}')

    def test_ok_wifi(self):
        app = self.app
        session = self.db_slave_session
        wifis = [
            Wifi(key="A1", lat=10000000, lon=10000000),
            Wifi(key="B2", lat=10020000, lon=10040000),
            Wifi(key="C3", lat=None, lon=None),
        ]
        session.add_all(wifis)
        session.commit()
        res = app.post_json('/v1/search',
                            {"wifi": [
                                {"key": "A1"}, {"key": "B2"}, {"key": "C3"},
                            ]},
                            status=200)
        self.assertEqual(res.content_type, 'application/json')
        self.assertEqual(res.body, '{"status": "ok", "lat": 1.0010000, '
                                   '"lon": 1.0020000, "accuracy": 500}')

    def test_wifi_too_few_matches(self):
        app = self.app
        session = self.db_slave_session
        wifis = [
            Wifi(key="A1", lat=10000000, lon=10000000),
            Wifi(key="B2", lat=None, lon=None),
        ]
        session.add_all(wifis)
        session.commit()
        res = app.post_json('/v1/search',
                            {"wifi": [
                                {"key": "A1"}, {"key": "B2"}, {"key": "C3"},
                            ]},
                            status=200)
        self.assertEqual(res.content_type, 'application/json')
        self.assertEqual(res.body, '{"status": "not_found"}')

    def test_not_found(self):
        app = self.app
        res = app.post_json('/v1/search',
                            {"cell": [{"mcc": 1, "mnc": 2,
                                       "lac": 3, "cid": 4}]},
                            status=200)
        self.assertEqual(res.content_type, 'application/json')
        self.assertEqual(res.body, '{"status": "not_found"}')

    def test_wifi_not_found(self):
        app = self.app
        res = app.post_json('/v1/search', {"wifi": [
                            {"key": "abcd"}, {"key": "cdef"}]},
                            status=200)
        self.assertEqual(res.content_type, 'application/json')
        self.assertEqual(res.body, '{"status": "not_found"}')

    def test_error(self):
        app = self.app
        res = app.post_json('/v1/search', {"cell": []}, status=400)
        self.assertEqual(res.content_type, 'application/json')
        self.assertTrue('errors' in res.json)
        self.assertFalse('status' in res.json)

    def test_error_unknown_key(self):
        app = self.app
        res = app.post_json('/v1/search', {"foo": 0}, status=400)
        self.assertEqual(res.content_type, 'application/json')
        self.assertTrue('errors' in res.json)

    def test_error_no_mapping(self):
        app = self.app
        res = app.post_json('/v1/search', [1], status=400)
        self.assertEqual(res.content_type, 'application/json')
        self.assertTrue('errors' in res.json)

    def test_no_json(self):
        app = self.app
        res = app.post('/v1/search', "\xae", status=400)
        self.assertTrue('errors' in res.json)