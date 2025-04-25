''' metric class array '''
from .metric import Metric


class Array(Metric):
    ''' metric class array '''

    def setup(self):
        self.category = 'array'

    def gatherstats(self, tstart, tend):
        self.reset_metrics()
        if self.realtime:
            resp = self.con.performance.real_time.get_array_stats(tstart, tend, self.metrics)
        else:
            resp = self.con.performance.get_array_stats(metrics=self.metrics)
        self.valuedata = resp['result']
        self.process_metrics()
