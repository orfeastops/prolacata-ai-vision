import unittest,copy
from facility_placement_counter import Tracker,CONFIG,linear_sum_assignment
import numpy as np

class Tests(unittest.TestCase):
    def tracker(self):
        c=copy.deepcopy(CONFIG)
        c.update(source_polygon=[[100,100],[200,100],[200,200],[100,200]],
                 tank_polygon=[[250,100],[350,100],[350,200],[250,200]])
        return Tracker(c)
    def frame(self,tr,t,x,y=150,p=.9):
        return tr.update(t,[[x-10,y-10,x+10,y+10]],[p])
    def cycle(self,tr,base=0,y=150,occupied=True):
        for i,(x,p) in enumerate([(150,.9),(150,.9),(190,.9),(230,.9),(270,.9),(290,.9),(290,.1),(300,.1)]):
            self.frame(tr,base+i*.125,x,y,p if occupied else .1)
    def test_complete_hand_cycle_has_unknown_block_quantity(self):
        t=self.tracker();self.cycle(t)
        self.assertEqual([e['predicted_quantity'] for e in t.events],[None])
        self.assertEqual(t.events[0]['status'],'candidate_deposit_quantity_unknown')
        self.assertIsNone(t.events[0]['certified_quantity'])
    def test_stationary_repeat_does_not_recount(self):
        t=self.tracker();self.cycle(t)
        for i in range(9,30):self.frame(t,i*.125,300,p=.1)
        self.assertEqual(len(t.events),1)
        self.assertIsNone(t.events[0]['predicted_quantity'])
    def test_empty_hand_motion_does_not_count(self):
        t=self.tracker();self.cycle(t,occupied=False);t.close(1)
        self.assertEqual(t.events,[])
    def test_lost_carry_is_unresolved(self):
        t=self.tracker();self.frame(t,0,150);self.frame(t,.125,150);t.update(1,[],[])
        self.assertEqual(len(t.events),1);self.assertIsNone(t.events[0]['predicted_quantity'])
    def test_video_end_does_not_assume_release(self):
        t=self.tracker();self.frame(t,0,150);self.frame(t,.125,150);t.close(.25)
        self.assertEqual(t.events[0]['status'],'unresolved_video_boundary')
        self.assertIsNone(t.events[0]['predicted_quantity'])
    def test_tank_only_rearrangement_does_not_arm(self):
        t=self.tracker()
        for i in range(20):self.frame(t,i*.125,280,p=.9 if i<10 else .1)
        self.assertEqual(t.events,[])
    def test_two_hands_do_not_establish_two_blocks(self):
        t=self.tracker()
        for i,(x,p) in enumerate([(150,.9),(150,.9),(190,.9),(230,.9),(270,.9),(290,.9),(290,.1),(300,.1)]):
            t.update(i*.125,[[x-8,120,x+8,136],[x-8,170,x+8,186]],[p,p])
        self.assertEqual(len(t.events),2)
        self.assertTrue(all(e['predicted_quantity'] is None for e in t.events))
    def test_matcher_can_leave_false_detection_unmatched(self):
        a,b=linear_sum_assignment(np.array([[2.,90.],[90.,3.]]));self.assertEqual(list(zip(a,b)),[(0,0),(1,1)])
        a,b=linear_sum_assignment(np.array([[100.]]));self.assertEqual(a,[])

if __name__=='__main__':unittest.main()
