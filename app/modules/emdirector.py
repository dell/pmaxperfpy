''' metric class emdirector '''
from .metric import Metric


class EmDirector(Metric):
    ''' metric class emdirector '''

    def setup(self):
        self.have_instances = True
        self.category = 'em_director'

    def updateobjectkeys(self):
        if self.realtime:
            objs = self.con.performance.real_time.get_em_director_keys()
        else:
            objs = self.con.performance.get_em_director_keys()
            objs = self.extract_id_field('directorId', objs)
        self.instances = objs

    def gatherstats(self, tstart, tend):
        self.reset_metrics()
        instances = {}
        for inst in self.instances:
            if self.realtime:
                resp = self.con.performance.real_time.get_em_director_stats(tstart, tend, self.metrics, inst)
            else:
                resp = self.con.performance.get_em_director_stats(inst, metrics=self.metrics)
            instances[inst] = resp['result']
        self.valuedata = instances
        self.process_metrics()
