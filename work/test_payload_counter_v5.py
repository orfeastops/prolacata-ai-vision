"""Counting/state/split invariants; passing these does not prove vision accuracy."""
import unittest,json
import numpy as np
from evaluate_payload_counter_v5 import Counter,OUT
class PayloadTests(unittest.TestCase):
    def detection(self,x,y,q=2):return dict(bbox=[x-25,y-18,x+25,y+18],confidence=.9,quantity=q)
    def trajectory(self,points,q=2):
        c=Counter();points=list(points)
        for n,(x,y) in enumerate(points):c.step(n*.1,[self.detection(x,y,q)])
        c.step(len(points)*.1+.5,[])
        return c
    def test_sustained_visible_load_counted_once(self):
        c=self.trajectory(zip(np.linspace(350,220,20),np.linspace(250,190,20)))
        self.assertEqual(sum(e['predicted_quantity'] for e in c.events),2)
        self.assertEqual(len(c.events),1)
    def test_stationary_cheese_does_not_increment(self):
        c=self.trajectory([(220,200)]*20)
        self.assertFalse(c.events)
    def test_load_moved_to_scraps_is_not_a_tank_deposit(self):
        c=self.trajectory(zip(np.linspace(350,440,20),np.linspace(250,80,20)))
        self.assertFalse(c.events)
    def test_unknown_quantity_is_not_silently_two(self):
        c=self.trajectory(zip(np.linspace(350,220,20),np.linspace(250,190,20)),0)
        self.assertFalse(c.events)
        self.assertIn('quantity_uncertain',c.rejected[0]['reasons'])
    def test_two_simultaneous_loads_do_not_share_an_id(self):
        c=Counter()
        for n in range(20):
            p=n/19;c.step(n*.1,[self.detection(350-120*p,230-65*p),self.detection(240-95*p,290-55*p)])
        c.step(2.5,[])
        self.assertEqual(sum(e['predicted_quantity'] for e in c.events),4)
    def test_clip_cutoff_is_not_a_release(self):
        c=Counter()
        for n in range(20):c.step(n*.1,[self.detection(350-n*6,250-n*3)])
        c.finish(1.9)
        self.assertFalse(c.events)
        self.assertIn('track_continues_at_clip_end',c.rejected[0]['reasons'])
    def test_training_sources_separate_and_no_unreviewed_background(self):
        m=json.loads((OUT/'dataset_manifest.json').read_text())
        train={r['source_sha256'] for r in m['rows'] if r['split']=='train'}
        val={r['source_sha256'] for r in m['rows'] if r['split']=='val'}
        self.assertFalse(train&val);self.assertFalse(train&set(m['forbidden_sources']))
        self.assertTrue(all(r['provenance']=='assistant_visual_anchor' for r in m['rows'] if not r['labels']))
        self.assertTrue(all(abs(r['time_s'])<40 for r in m['rows']))
if __name__=='__main__':unittest.main()
