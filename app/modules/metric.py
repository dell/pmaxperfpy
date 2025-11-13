''' base class for metrics '''
import prometheus_client


class Metric():
    '''base class for metrics'''

    def gather_values(self):
        ''' gather current metric values '''
        raise NotImplementedError

    def setup(self):
        ''' setup instance, called by parent constructor '''
        raise NotImplementedError

    def __init__(self, pmax, config, global_metrics, thread_lock):
        '''	constructor '''
        self.pmax = pmax
        self.config = config
        self._metrics = global_metrics
        self.thread_lock = thread_lock
        self.category = None
        self.metric_names = {}
        self.setup()

    def parse_metrics(self):
        ''' gather values and process into prometheus Gauges '''
        instance_count = 0
        for element in self.gather_values():
            tags = self.config["tags"].copy()
            tags[self.category] = element["id"]
            instance_count += 1
            for key, value in self.metric_names.items():
                full_name = f'powermax_{self.category}_{key}'

                if full_name in self._metrics:
                    p_metric = self._metrics[full_name]
                else:
                    with self.thread_lock:
                        p_metric = prometheus_client.Gauge(full_name, '', labelnames=tags.keys())
                        self._metrics[full_name] = p_metric
                p_metric.labels(**tags).set_to_current_time()
                p_metric.labels(**tags).set(element[value])
        return (len(self.metric_names), instance_count)
