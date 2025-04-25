''' metric class beport '''
from .metric import Metric


class BePort(Metric):
    ''' metric class beport '''

    def setup(self):
        self.have_instances = True
        self.category = 'backend_port'

    def updateobjectkeys(self):
        if self.realtime:
            objs = self.con.performance.real_time.get_backend_port_keys()
        else:
            objs = []
            directors = self.con.performance.get_backend_director_keys()
            for bedir in self.extract_id_field('directorId', directors):
                ports = self.con.performance.get_backend_port_keys(bedir)
                for port in self.extract_id_field('portId', ports):
                    objs.append(bedir + ":" + port)
        self.instances = objs

    def gatherstats(self, tstart, tend):
        self.reset_metrics()
        valuedata = {}
        for inst in self.instances:
            if self.realtime:
                resp = self.con.performance.real_time.get_backend_port_stats(tstart, tend, self.metrics, inst)
            else:
                (bedir, port) = inst.split(":")
                resp = self.con.performance.get_backend_port_stats(bedir, port, metrics=self.metrics)
            valuedata[inst] = resp['result']
        self.valuedata = valuedata
        self.process_metrics()
