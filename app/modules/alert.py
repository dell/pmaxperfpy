''' alert metric class '''
import time
from .metric import Metric


class Alert(Metric):
    ''' alert metric class '''

    def setup(self):
        self.category = 'alert'
        if not hasattr(self.con.system, 'get_alert_summary'):
            raise ValueError('Alerts not supported with this API version')

    def gatherstats(self, tstart, tend):
        self.reset_metrics()
        alerts = self.con.system.get_alert_summary()
        array_alerts = alerts['symmAlertSummary'][0]['arrayAlertSummary']
        array_alerts.update(alerts['symmAlertSummary'][0]['performanceAlertSummary'])
        array_alerts['timestamp'] = int(time.time() * 1000)
        self.valuedata = [array_alerts]
        self.process_metrics()
