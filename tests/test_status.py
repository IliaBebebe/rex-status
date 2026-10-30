import unittest
from datetime import datetime, timedelta, timezone
from status_model import compose

class StatusTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 30, 12, tzinfo=timezone.utc)
        self.stamp = self.now.isoformat()
        self.services = [dict(id='site',name='Site',description='',group='web'),dict(id='bot',name='Bot',description='',group='telegram')]
        self.incidents = [dict(active=True,affectedGroups=['web'])]
        self.probes = {'site':dict(ok=True,checkedAt=self.stamp)}
    def make(self, heartbeat=None, probes=None, incidents=None):
        return compose(self.services,self.incidents if incidents is None else incidents,self.probes if probes is None else probes,heartbeat,self.now)['services']
    def test_healthy_probe_cannot_clear_known_regional_incident(self):
        self.assertEqual(self.make()[0]['status'],'limited')
    def test_missing_bot_heartbeat_is_unknown(self):
        self.assertEqual(self.make()[1]['status'],'unknown')
    def test_expired_and_future_heartbeat_cannot_claim_working(self):
        for offset in (-36, 2):
            stamp=(self.now+timedelta(minutes=offset)).isoformat()
            self.assertEqual(self.make(dict(checkedAt=stamp,services={'bot':'operational'}))[1]['status'],'unknown')
    def test_fresh_bot_probe_is_independent_from_web_incident(self):
        rows=self.make(dict(checkedAt=self.stamp,services={'bot':'operational'}))
        self.assertEqual([r['status'] for r in rows],['limited','operational'])
    def test_failed_site_probe_overrides_regional_warning(self):
        self.assertEqual(self.make(probes={'site':dict(ok=False,checkedAt=self.stamp)})[0]['status'],'outage')
    def test_stale_external_probe_cannot_claim_down_or_healthy(self):
        self.assertEqual(self.make(probes={'site':dict(ok=True,checkedAt=(self.now-timedelta(hours=1)).isoformat())})[0]['status'],'unknown')
    def test_resolving_incident_allows_positive_probe(self):
        self.assertEqual(self.make(incidents=[])[0]['status'],'operational')
    def test_local_failure_cannot_be_hidden_by_external_cached_success(self):
        self.assertEqual(self.make(dict(checkedAt=self.stamp,services={'site':'outage'}))[0]['status'],'outage')

if __name__=='__main__':unittest.main()
