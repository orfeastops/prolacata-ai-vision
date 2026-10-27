"""Checks algorithm bookkeeping only, not camera recognition accuracy."""
import unittest
from evaluate_block_trajectories import HypothesisTracker, CONFIG


class HypothesisTests(unittest.TestCase):
    def tracker(self):
        return HypothesisTracker(dict(CONFIG, source_polygon=[[0,0],[100,0],[100,180],[0,180]],
            tank_polygon=[[120,0],[220,0],[220,180],[120,180]]))

    def run_path(self, count=1, cls=0, close=False, unknown_at=None, duplicate=False):
        tracker=self.tracker()
        for i,x in enumerate([30,50,90,140,180]):
            ds=[dict(box=[x-4,y-4,x+4,y+4],cls=cls,confidence=.9) for y in [20,80,140][:count]]
            if i==unknown_at: ds[0]['cls']=1
            if duplicate: ds.append(dict(ds[0]))
            tracker.update(i/8,ds)
        if close: tracker.close()
        else: tracker.update(1.125,[])
        return tracker

    def test_one_two_three_objects_not_number_of_hands(self):
        for n in [1,2,3]:
            tracker=self.run_path(count=n)
            self.assertEqual(sum(e['candidate_quantity'] or 0 for e in tracker.events),n)
            tracker.update(2,[])
            self.assertEqual(sum(e['candidate_quantity'] or 0 for e in tracker.events),n)

    def test_any_unknown_quantity_abstains(self):
        self.assertIsNone(self.run_path(unknown_at=2).events[0]['candidate_quantity'])

    def test_overlapping_detections_do_not_double_count(self):
        tracker=self.run_path(duplicate=True)
        self.assertEqual(sum(e['candidate_quantity'] or 0 for e in tracker.events),0)

    def test_boundary_is_not_release(self):
        self.assertIsNone(self.run_path(close=True).events[0]['candidate_quantity'])

    def test_disappearance_outside_tank_is_not_counted(self):
        tracker=self.tracker()
        for i,x in enumerate([30,50,90]):
            tracker.update(i/8,[dict(box=[x-4,16,x+4,24],cls=0,confidence=.9)])
        tracker.update(1,[])
        self.assertIsNone(tracker.events[0]['candidate_quantity'])

    def test_no_cheese_observations_no_hypotheses(self):
        tracker=self.tracker()
        for i in range(20): tracker.update(i/8,[])
        tracker.close()
        self.assertEqual(tracker.events,[])

if __name__=='__main__':unittest.main()
