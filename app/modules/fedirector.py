''' metric class fedirector '''
from .metric import Metric


class FeDirector(Metric):
    ''' metric class fedirector '''

    def setup(self):
        self.have_instances = True
        self.category = 'frontend_director'

    def updateobjectkeys(self):
        if self.realtime:
            objs = self.con.performance.real_time.get_frontend_director_keys()
        else:
            objs = self.con.performance.get_frontend_director_keys()
            objs = self.extract_id_field('directorId', objs)
        self.instances = objs

    def gatherstats(self, tstart, tend):
        self.reset_metrics()
        instances = {}
        for inst in self.instances:
            if self.realtime:
                resp = self.con.performance.real_time.get_frontend_director_stats(tstart, tend, self.metrics, inst)
            else:
                resp = self.con.performance.get_frontend_director_stats(inst, metrics=self.metrics)
            instances[inst] = resp['result']
        self.valuedata = instances
        self.process_metrics()
