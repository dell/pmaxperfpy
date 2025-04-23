''' metric class iscsitarget '''
from .metric import Metric


class IscsiTarget(Metric):
    ''' metric class iscsitarget '''

    def setup(self):
        self.have_instances = True
        self.category = 'iscsi_target'

    def updateobjectkeys(self):
        objs = self.con.performance.get_iscsi_target_keys()
        objs = self.extract_id_field('iscsiTargetId', objs)
        self.instances = objs

    def gatherstats(self, tstart, tend):
        self.reset_metrics()
        valuedata = {}
        for inst in self.instances:
            resp = self.con.performance.get_iscsi_target_stats(inst, metrics=self.metrics)
            valuedata[inst] = resp['result']
        self.valuedata = valuedata
        self.process_metrics()
