import re
import sys
import threading
import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import PyU4V

sys.path.append('app')
import pmaxperf
from modules.alerts import Alerts, ALERT_METRIC_NAME, ALERT_LABEL_NAMES

cfg = {
    'hostname': 'local',
    'username': 'user',
    'password': 'secret',
    'unisphere_port': 1234,
    'verify': True
}

class ConfigTests(unittest.TestCase):

    def test_connection(self):
        PyU4V.U4VConn = Mock()
        PyU4V.U4VConn.return_value = "call_ok"
        self.assertEqual(pmaxperf.connect_unisphere(cfg), "call_ok")
        PyU4V.U4VConn.assert_called_once()


class AlertsCreatedDateTests(unittest.TestCase):

    def test_format_matches_pyu4v_spec(self):
        '''created_date string matches >MMM-dd-yyyy HH:mm:ss.000'''
        result = Alerts.calculate_created_date(900)
        self.assertTrue(result.startswith('>'))
        pattern = r'^>[A-Z][a-z]{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2}\.000$'
        self.assertRegex(result, pattern)

    def test_time_offset_is_correct(self):
        '''cutoff time is approximately interval seconds in the past'''
        result = Alerts.calculate_created_date(900)
        date_str = result[1:]
        parsed = datetime.strptime(date_str, '%b-%d-%Y %H:%M:%S.000')
        expected = datetime.now() - timedelta(seconds=900)
        diff = abs((parsed - expected).total_seconds())
        self.assertLess(diff, 5)

    def test_different_intervals(self):
        '''different interval values produce different cutoff times'''
        result_short = Alerts.calculate_created_date(60)
        result_long = Alerts.calculate_created_date(3600)
        short_date = datetime.strptime(result_short[1:], '%b-%d-%Y %H:%M:%S.000')
        long_date = datetime.strptime(result_long[1:], '%b-%d-%Y %H:%M:%S.000')
        self.assertGreater(short_date, long_date)


class AlertsFetchTests(unittest.TestCase):

    def _make_alerts_instance(self, alert_cfg=None):
        '''helper to create an Alerts instance with mocks'''
        mock_pmax = Mock()
        test_cfg = {
            'serial': '000123456789',
            'alerts': alert_cfg or {'enabled': True, 'interval': 900}
        }
        return Alerts(mock_pmax, test_cfg, {}, threading.Lock(),
                      threading.Event(), 5, Mock()), mock_pmax

    def test_passes_severity_and_type_filters(self):
        '''configured severity and type are forwarded to get_alert_ids'''
        alerts_obj, mock_pmax = self._make_alerts_instance({
            'enabled': True, 'interval': 900,
            'severity': 'WARNING', 'type': 'ARRAY'
        })
        mock_pmax.system.get_alert_ids.return_value = []
        alerts_obj._fetch_alerts()

        call_kwargs = mock_pmax.system.get_alert_ids.call_args[1]
        self.assertEqual(call_kwargs['array'], '000123456789')
        self.assertEqual(call_kwargs['severity'], 'WARNING')
        self.assertEqual(call_kwargs['_type'], 'ARRAY')
        self.assertIn('created_date', call_kwargs)

    def test_omits_optional_filters_when_not_configured(self):
        '''severity and type are omitted when not in config'''
        alerts_obj, mock_pmax = self._make_alerts_instance({
            'enabled': True, 'interval': 900
        })
        mock_pmax.system.get_alert_ids.return_value = []
        alerts_obj._fetch_alerts()

        call_kwargs = mock_pmax.system.get_alert_ids.call_args[1]
        self.assertNotIn('severity', call_kwargs)
        self.assertNotIn('_type', call_kwargs)

    def test_returns_empty_list_when_no_alerts(self):
        '''returns empty list when get_alert_ids returns nothing'''
        alerts_obj, mock_pmax = self._make_alerts_instance()
        mock_pmax.system.get_alert_ids.return_value = []
        result = alerts_obj._fetch_alerts()

        self.assertEqual(result, [])
        mock_pmax.system.get_alert_details.assert_not_called()

    def test_fetches_details_for_each_alert(self):
        '''get_alert_details is called for every returned alert id'''
        alerts_obj, mock_pmax = self._make_alerts_instance()
        mock_pmax.system.get_alert_ids.return_value = ['100', '200', '300']
        mock_pmax.system.get_alert_details.side_effect = [
            {'alertId': '100'}, {'alertId': '200'}, {'alertId': '300'}
        ]
        result = alerts_obj._fetch_alerts()

        self.assertEqual(len(result), 3)
        self.assertEqual(mock_pmax.system.get_alert_details.call_count, 3)


class AlertsMetricsTests(unittest.TestCase):

    def _make_alerts_instance(self):
        '''helper to create Alerts instance with mocked gauge'''
        mock_pmax = Mock()
        test_cfg = {
            'serial': '000123456789',
            'alerts': {'enabled': True, 'interval': 900}
        }
        metrics = {}
        return Alerts(mock_pmax, test_cfg, metrics, threading.Lock(),
                      threading.Event(), 5, Mock()), metrics

    @patch('modules.alerts.prometheus_client.Gauge')
    def test_creates_gauge_on_first_call(self, mock_gauge_cls):
        '''gauge is created with correct name and labels on first update'''
        alerts_obj, metrics = self._make_alerts_instance()
        mock_gauge = Mock()
        mock_gauge_cls.return_value = mock_gauge

        test_alerts = [{'alertId': '1', 'severity': 'WARNING', 'type': 'ARRAY',
                        'state': 'NEW', 'object': 'SRP_0', 'object_type': 'SRP',
                        'description': 'test alert', 'created_date': '1234567890'}]
        alerts_obj._update_metrics(test_alerts)

        mock_gauge_cls.assert_called_once_with(
            ALERT_METRIC_NAME, 'PowerMax active alerts',
            labelnames=ALERT_LABEL_NAMES
        )
        self.assertIn(ALERT_METRIC_NAME, metrics)

    @patch('modules.alerts.prometheus_client.Gauge')
    def test_sets_gauge_value_for_each_alert(self, mock_gauge_cls):
        '''gauge.labels().set(1) is called for each alert'''
        alerts_obj, metrics = self._make_alerts_instance()
        mock_gauge = Mock()
        mock_gauge_cls.return_value = mock_gauge

        test_alerts = [
            {'alertId': '1', 'severity': 'WARNING', 'type': 'ARRAY',
             'state': 'NEW', 'object': 'SRP_0', 'object_type': 'SRP',
             'description': 'alert one', 'created_date': '111'},
            {'alertId': '2', 'severity': 'CRITICAL', 'type': 'ARRAY',
             'state': 'NEW', 'object': 'SRP_1', 'object_type': 'SRP',
             'description': 'alert two', 'created_date': '222'}
        ]
        alerts_obj._update_metrics(test_alerts)

        self.assertEqual(mock_gauge.labels.return_value.set.call_count, 2)
        self.assertEqual(len(alerts_obj._previous_label_sets), 2)

    @patch('modules.alerts.prometheus_client.Gauge')
    def test_removes_stale_alerts(self, mock_gauge_cls):
        '''alerts from previous cycle that are gone are removed from gauge'''
        alerts_obj, metrics = self._make_alerts_instance()
        mock_gauge = Mock()
        mock_gauge_cls.return_value = mock_gauge

        # first cycle: one alert
        alerts_obj._update_metrics([
            {'alertId': '1', 'severity': 'WARNING', 'type': 'ARRAY',
             'state': 'NEW', 'object': 'SRP_0', 'object_type': 'SRP',
             'description': 'alert one', 'created_date': '111'}
        ])
        self.assertEqual(len(alerts_obj._previous_label_sets), 1)

        # second cycle: no alerts - stale one should be removed
        alerts_obj._update_metrics([])
        mock_gauge.remove.assert_called_once()
        self.assertEqual(len(alerts_obj._previous_label_sets), 0)

    @patch('modules.alerts.prometheus_client.Gauge')
    def test_default_interval_is_900(self, mock_gauge_cls):
        '''interval defaults to 900 when not specified'''
        mock_pmax = Mock()
        test_cfg = {'serial': '000123456789', 'alerts': {'enabled': True}}
        alerts_obj = Alerts(mock_pmax, test_cfg, {}, threading.Lock(),
                            threading.Event(), 5, Mock())
        self.assertEqual(alerts_obj.interval, 900)
