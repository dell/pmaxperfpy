''' custom prometheus collector '''
import prometheus_client


class PromCollector():
    ''' custom prometheus collector '''

    def __init__(self, name, tagnames):
        '''constructor'''
        self.name = name
        self.tagnames = list(tagnames)
        self.gauge = prometheus_client.metrics_core.GaugeMetricFamily(self.name, '', labels=self.tagnames)
        prometheus_client.REGISTRY.register(self)

    def store(self, value, timestamp, labelvalues):
        '''store metric values with timestamps'''
        self.gauge.add_metric(list(labelvalues), value, int(timestamp / 1000))

    def setvalue(self, value, timestamp, labelvalues):
        '''clear old values and store'''
        self.clear()
        self.store(value, timestamp, labelvalues)

    def collect(self):
        '''retrieve values (called by Prom registry)'''
        yield self.gauge

    def clear(self):
        '''explict clear old values'''
        self.gauge.samples = []
