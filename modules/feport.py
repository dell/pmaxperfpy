''' metric class feport '''
from .metric import Metric


class FePort(Metric):
    ''' metric class feport '''

    def setup(self):
        self.have_instances = True
        self.category = 'frontend_port'

    def updateobjectkeys(self):
        if self.realtime:
            objs = self.con.performance.real_time.get_frontend_port_keys()
        else:
            objs = []
            directors = self.con.performance.get_frontend_director_keys()
            for fedir in self.extract_id_field('directorId', directors):
                ports = self.con.performance.get_frontend_port_keys(fedir)
                for port in self.extract_id_field('portId', ports):
                    objs.append(fedir + ":" + port)
        self.instances = objs

    def gatherstats(self, tstart, tend):
        self.reset_metrics()
        instances = {}
        for inst in self.instances:
            if self.realtime:
                resp = self.con.performance.real_time.get_frontend_port_stats(tstart, tend, self.metrics, inst)
            else:
                (fedir, port) = inst.split(":")
                resp = self.con.performance.get_frontend_port_stats(fedir, port, metrics=self.metrics)
            instances[inst] = resp['result']
        self.valuedata = instances
        self.process_metrics()
