''' metric class volumes '''
from .metric import Metric


class Volumes(Metric):
    ''' metric class volumes (capacity) '''

    def setup(self):
        ''' setup instance, called by parent constructor '''
        self.category = 'Volumes'
        self.metric_names = {
            'CapacityGB': 'cap_gb',
            'UnreducibleDataGB': 'unreducible_data_gb',
            'DataReductionRatio': 'data_reduction_ratio_to_one',
            'EffectiveUsedCapacityGB': 'effective_used_capacity_gb'
        }

    def gather_values(self):
        ''' gather current metric values '''
        return self.pmax.volumes.get_volumes_details()["volumes"]
