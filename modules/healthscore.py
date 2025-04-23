''' alert metric class '''
import time
from .metric import Metric


class HealthScore(Metric):
    ''' healthscore metric class
        {
           "num_failed_disks" : 0,
           "health_score_metric" : [
              {
                 "instance_metrics" : [
                    {
                       "health_score_instance_metric" : []
                    }
                 ],
                 "data_date" : 1620980414165,
                 "cached_date" : 1620980414165,
                 "metric" : "SERVICE_LEVEL_COMPLIANCE",
                 "expired" : false,
                 "health_score" : 100
              },
           ]
        }
    '''

    SCORES = ['SERVICE_LEVEL_COMPLIANCE', 'OVERALL', 'CAPACITY', 'CONFIGURATION', 'SYSTEM_UTILIZATION', 'STORAGE_GROUP_RESPONSE_TIME']

    def setup(self):
        self.category = 'healthscore'
        if not hasattr(self.con.system, 'get_system_health'):
            raise ValueError('Healthscore not supported with this API version')

    def get_score_value(self, pattern, listofdict):  # pylint: disable=no-self-use
        ''' filter for one dict element by name '''
        for elem in listofdict:
            if elem['metric'] == pattern:
                return int(elem['health_score'])
        return 0

    def gatherstats(self, tstart, tend):
        self.reset_metrics()
        healthscore = {}
        result = self.con.system.get_system_health()
        metrics = result['health_score_metric']
        healthscore = {
            'timestamp': int(time.time() * 1000),
            'failed_disks': result['num_failed_disks']
        }
        for scoretype in HealthScore.SCORES:
            healthscore[scoretype.lower()] = self.get_score_value(scoretype, metrics)
        self.valuedata = [healthscore]
        self.process_metrics()
