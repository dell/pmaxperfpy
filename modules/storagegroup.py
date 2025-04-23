''' metric class storagegroup '''
from .metric import Metric


class StorageGroup(Metric):
    ''' metric class storagegroup (capacity) '''

    def setup(self):
        ''' setup instance, called by parent constructor '''
        self.category = 'StorageGroup'
        self.metric_names = {
            'CapacityGB': 'cap_gb',
            'UnreducibleDataGB': 'unreducible_data_gb',
            'DataReductionRatio': 'data_reduction_ratio_to_one',
            'EffectiveUsedCapacityGB': 'effective_used_capacity_gb'
        }

    def gather_values(self):
        ''' gather current metric values '''
        return self.pmax.storage_groups.get_storage_groups_details()["storage_groups"]
