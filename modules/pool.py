''' metric class pool '''
import time

from .metric import Metric


class Pool(Metric):
    ''' metric class pool '''

    def setup(self):
        self.have_instances = True
        self.category = 'pool'

    def updateobjectkeys(self):
        objs = self.con.provisioning.get_srp_list()
        self.instances = objs

    def gatherstats(self, tstart, tend):
        self.reset_metrics()
        instances = {}
        for inst in self.instances:
            resp = self.con.provisioning.get_srp(inst)
            poolinfo = resp['srp_capacity']
            efficiency = resp['srp_efficiency']
            del efficiency['compression_state']
            poolinfo.update(efficiency)
            poolinfo['timestamp'] = int(time.time() * 1000)
            instances[inst] = [poolinfo]
        self.valuedata = instances
        self.process_metrics()
