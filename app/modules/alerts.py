''' alerts collector module '''
import logging
import time
from datetime import datetime, timedelta
from itertools import product

import prometheus_client
from requests.exceptions import RequestException


MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

ALERT_LABEL_NAMES = [
    'serial', 'alert_id', 'severity', 'type', 'state',
    'object', 'object_type', 'description', 'created_date'
]

ALERT_METRIC_NAME = 'powermax_alert_active'


class Alerts():
    ''' alerts collector - fetches alerts from Unisphere and exposes as Prometheus metrics '''

    def __init__(self, pmax, cfg, global_metrics, thread_lock, stop_event,
                 sleep_interval, reconnect_fn):
        ''' constructor '''
        self.pmax = pmax
        self.cfg = cfg
        self._metrics = global_metrics
        self.thread_lock = thread_lock
        self.stop_event = stop_event
        self.sleep_interval = sleep_interval
        self.reconnect_fn = reconnect_fn
        self.alert_cfg = cfg.get('alerts', {})
        self.interval = self.alert_cfg.get('interval', 900)
        self._previous_label_sets = set()

    @staticmethod
    def calculate_created_date(interval):
        ''' calculate created_date filter string for alerts created since last interval '''
        cutoff = datetime.now() - timedelta(seconds=interval)
        month = MONTHS[cutoff.month - 1]
        return f'>{month}-{cutoff.strftime("%d-%Y %H:%M:%S.000")}'

    def _build_filter_combinations(self):
        ''' build list of (severity, type) filter dicts from the cartesian product of configured values '''
        severities = self.alert_cfg.get('severity', [None])
        types = self.alert_cfg.get('type', [None])
        combinations = []
        for sev, typ in product(severities, types):
            filt = {}
            if sev is not None:
                filt['severity'] = sev
            if typ is not None:
                filt['_type'] = typ
            combinations.append(filt)
        return combinations

    def _fetch_alerts(self):
        ''' fetch alert ids and their details from Unisphere '''
        base_kwargs = {
            'array': self.cfg.get('serial'),
            'created_date': self.calculate_created_date(self.interval)
        }
        seen_ids = set()
        alerts = []
        for filt in self._build_filter_combinations():
            kwargs = {**base_kwargs, **filt}
            alert_ids = self.pmax.system.get_alert_ids(**kwargs)
            if not alert_ids:
                continue
            for alert_id in alert_ids:
                if alert_id in seen_ids:
                    continue
                seen_ids.add(alert_id)
                try:
                    details = self.pmax.system.get_alert_details(alert_id)
                    if details:
                        alerts.append(details)
                except RequestException as err:
                    logging.warning('Failed to get details for alert %s: %s', alert_id, str(err))
        return alerts

    def _update_metrics(self, alerts):
        ''' update prometheus metrics with current alerts, clearing stale ones '''
        if ALERT_METRIC_NAME not in self._metrics:
            with self.thread_lock:
                if ALERT_METRIC_NAME not in self._metrics:
                    self._metrics[ALERT_METRIC_NAME] = prometheus_client.Gauge(
                        ALERT_METRIC_NAME, 'PowerMax active alerts',
                        labelnames=ALERT_LABEL_NAMES
                    )
        gauge = self._metrics[ALERT_METRIC_NAME]

        current_label_sets = set()
        for alert in alerts:
            labels = {
                'serial': self.cfg.get('serial', ''),
                'alert_id': str(alert.get('alertId', '')),
                'severity': alert.get('severity', ''),
                'type': alert.get('type', ''),
                'state': alert.get('state', ''),
                'object': alert.get('object', ''),
                'object_type': alert.get('object_type', ''),
                'description': alert.get('description', ''),
                'created_date': str(alert.get('created_date', ''))
            }
            label_tuple = tuple(labels[k] for k in ALERT_LABEL_NAMES)
            current_label_sets.add(label_tuple)
            gauge.labels(**labels).set(1)

        # remove stale alerts from previous cycle
        stale = self._previous_label_sets - current_label_sets
        for label_tuple in stale:
            try:
                gauge.remove(*label_tuple)
            except KeyError:
                pass

        self._previous_label_sets = current_label_sets

    def run_loop(self):
        ''' main alert collection loop '''
        serial = self.cfg.get('serial', 'unknown')
        logging.info('%s: starting alert collection (interval=%ds)', serial, self.interval)

        counter = self.interval  # trigger immediately on first run
        while self.pmax and not self.stop_event.is_set():
            if counter < self.interval:
                counter += self.sleep_interval
                time.sleep(self.sleep_interval)
                continue
            counter = 0
            iteration_start = time.time()
            try:
                alerts = self._fetch_alerts()
                self._update_metrics(alerts)
                logging.info('%s: collected %d alerts', serial, len(alerts))
            except RequestException as err:
                logging.error('%s alert collection error: %s', serial, str(err))
                self.pmax = self.reconnect_fn(self.cfg, serial)

            duration = time.time() - iteration_start
            sleep_time = float(self.sleep_interval - duration % self.sleep_interval)
            counter += duration + sleep_time
            time.sleep(sleep_time)
        logging.info('%s stopping alert collection', serial)
