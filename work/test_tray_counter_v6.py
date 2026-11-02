import unittest
import numpy as np
from persistent_payload_tracker_v6 import PersistentCounter, minimum_assignment
from tray_inventory_gate_v6 import InventoryGate, InventoryObservation


def detection(x,y,q=2):
    return dict(bbox=[x-20,y-15,x+20,y+15],confidence=.9,quantity=q)


class TrackerTests(unittest.TestCase):
    def test_global_assignment_avoids_greedy_trap(self):
        cost=np.array([[1,2,125,1e6],[1.1,100,1e6,125]])
        result=minimum_assignment(cost)
        self.assertEqual(sum(cost[i,j] for i,j in result),3.1)

    def test_occlusion_keeps_same_load(self):
        c=PersistentCounter()
        for i in range(6):c.step(i*.1,[detection(350-8*i,250-4*i)])
        ident=next(iter(c.active))
        for t in [.6,.7,.8,.9,1.0]:c.step(t,[])
        out=c.step(1.1,[detection(285,218)])
        self.assertEqual(out[0]['track_id'],ident)
        self.assertEqual(len(c.active),1)
        self.assertFalse(c.events)

    def test_lost_track_is_not_joined_forever(self):
        c=PersistentCounter();c.step(0,[detection(350,250)])
        out=c.step(2,[detection(350,250)])
        self.assertEqual(out[0]['track_id'],2)

    def test_return_to_source_creates_new_load(self):
        c=PersistentCounter()
        for n in range(20):c.step(n*.1,[detection(350-7*n,250-3*n)])
        out=c.step(2.6,[detection(340,250)])
        self.assertEqual(out[0]['track_id'],2)

    def test_two_simultaneous_loads_remain_separate(self):
        c=PersistentCounter()
        for n in range(20):
            out=c.step(n*.1,[detection(390-5*n,170-2*n),detection(310-5*n,320-2*n)])
            self.assertEqual(len({d['track_id'] for d in out}),2)
        c.step(3.5,[])
        self.assertEqual(len(c.events)+len(c.rejected),2)

    def test_disappearance_is_labeled_candidate(self):
        c=PersistentCounter()
        for n in range(20):c.step(n*.1,[detection(350-7*n,250-3*n)])
        c.step(3.2,[])
        self.assertEqual(len(c.events),1)
        self.assertFalse(c.events[0]['release_verified'])
        self.assertFalse(c.events[0]['source_inventory_verified'])

    def test_clip_end_cannot_commit(self):
        c=PersistentCounter()
        for n in range(20):c.step(n*.1,[detection(350-7*n,250-3*n)])
        c.finish(1.9)
        self.assertFalse(c.events)

    def test_stationary_or_reverse_motion_does_not_count(self):
        for points in [[(350,250)]*20,[(220+6*n,180+3*n) for n in range(20)]]:
            c=PersistentCounter()
            for n,p in enumerate(points):c.step(n*.1,[detection(*p)])
            c.step(3.2,[]);self.assertFalse(c.events)


class InventoryTests(unittest.TestCase):
    def gate(self,before=7,after=3,visible=True,tray_after='tray'):
        g=InventoryGate()
        g.observe(InventoryObservation('a','tray',0,before,True,True,'synthetic test'))
        g.observe(InventoryObservation('b',tray_after,2,after,visible,True,'synthetic test'))
        return g

    def test_two_workers_share_one_inventory_budget(self):
        g=self.gate();self.assertTrue(g.claim('L','a','b',2,1));self.assertTrue(g.claim('R','a','b',2,1))
        self.assertFalse(g.claim('duplicate','a','b',2,1))
        self.assertEqual(g.release('rL','L',2,3,'filling_tank','A',True),2)
        self.assertEqual(g.release('rR','R',2,3,'filling_tank','A',True),2)
        self.assertEqual(g.report()['evidence_supported_additions'],{'A':4})

    def test_same_tray_reposition_is_zero(self):
        g=self.gate(9,9)
        self.assertFalse(g.claim('move','a','b',1,1))
        self.assertEqual(g.release('r','move',1,3,'filling_tank','A',True),0)

    def test_occlusion_unknown_and_changed_tray_cannot_supply_budget(self):
        for g in [self.gate(after=None),self.gate(visible=False),self.gate(tray_after='other')]:
            self.assertFalse(g.claim('load','a','b',2,1))

    def test_empty_tray_before_release_stays_pending(self):
        g=self.gate(3,0);g.claim('load','a','b',3,1)
        self.assertEqual(g.report()['evidence_supported_additions'],{})
        self.assertEqual(g.release('disappeared','load',3,3,'filling_tank','A',False),0)
        self.assertEqual(g.release('first','load',1,4,'filling_tank','A',True),1)
        self.assertEqual(g.release('remaining','load',2,5,'filling_tank','A',True),2)
        self.assertEqual(g.release('remaining','load',2,5,'filling_tank','A',True),0)

    def test_crumb_or_tray_destination_never_increments(self):
        g=self.gate(2,0);g.claim('load','a','b',2,1)
        self.assertEqual(g.release('crumb','load',2,3,'crumb_tank','A',True),0)
        self.assertEqual(g.release('tray','load',2,3,'same_tray',None,True),0)
        self.assertEqual(g.release('stale','load',2,4,'filling_tank','A',True),0)

    def test_overlapping_inventory_cannot_supply_same_blocks_twice(self):
        g=self.gate(7,3);g.window('a','b')
        g.observe(InventoryObservation('c','tray',1,5,True,True,'synthetic test'))
        g.observe(InventoryObservation('d','tray',3,1,True,True,'synthetic test'))
        with self.assertRaises(ValueError):g.window('c','d')

    def test_no_fixed_ten_or_fixed_two(self):
        g=self.gate(7,0);self.assertTrue(g.claim('all','a','b',7,1))
        self.assertEqual(g.release('r','all',7,3,'filling_tank','A',True),7)

if __name__=='__main__':unittest.main(verbosity=2)
