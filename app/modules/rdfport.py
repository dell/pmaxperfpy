''' metric class rdfport '''
from .metric import Metric


class RdfPort(Metric):
    ''' metric class rdfport '''

    def setup(self):
        self.have_instances = True
        self.category = 'rdf_port'

    def updateobjectkeys(self):
        if self.realtime:
            objs = self.con.performance.real_time.get_rdf_port_keys()
        else:
            objs = []
            directors = self.con.performance.get_rdf_director_keys()
            for rdfdir in self.extract_id_field('directorId', directors):
                ports = self.con.performance.get_rdf_port_keys(rdfdir)
                for port in self.extract_id_field('portId', ports):
                    objs.append(rdfdir + ":" + port)
        self.instances = objs

    def gatherstats(self, tstart, tend):
        self.reset_metrics()
        instances = {}
        for inst in self.instances:
            if self.realtime:
                resp = self.con.performance.real_time.get_rdf_port_stats(tstart, tend, self.metrics, inst)
            else:
                (rdfdir, port) = inst.split(":")
                resp = self.con.performance.get_rdf_port_stats(rdfdir, port, metrics=self.metrics)
            instances[inst] = resp['result']
        self.valuedata = instances
        self.process_metrics()
