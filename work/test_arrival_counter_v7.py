import unittest
from arrival_counter_v7 import ArrivalCounter,group_detections

def scene(cheese=7,empty=3,unknown=0,duplicates=False):
    ds=[dict(class_id=2,bbox=[20,40,260,170],confidence=.95)]
    for n,cls in enumerate([0]*cheese+[1]*empty+[3]*unknown):
        x=35+(n%5)*44;y=65+(n//5)*60
        ds.append(dict(class_id=cls,bbox=[x,y,x+30,y+40],confidence=.9))
    if duplicates:ds.append(dict(ds[1],class_id=1,confidence=.3))
    return ds

class Tests(unittest.TestCase):
    def run_scene(self,ds):
        c=ArrivalCounter()
        for i in range(5):c.step(i*.08,ds,i)
        return c.finish()
    def test_seven_is_seven_not_ten(self):self.assertEqual(self.run_scene(scene())[0]['count'],7)
    def test_nine_is_nine(self):self.assertEqual(self.run_scene(scene(9,1))[0]['count'],9)
    def test_empty_plate_zero(self):self.assertEqual(self.run_scene(scene(0,10))[0]['count'],0)
    def test_incomplete_positions_are_unknown(self):self.assertIsNone(self.run_scene(scene(7,2))[0]['count'])
    def test_occlusion_is_not_empty(self):self.assertIsNone(self.run_scene(scene(7,2,1))[0]['count'])
    def test_cross_class_duplicate_is_not_another_position(self):
        self.assertEqual(self.run_scene(scene(7,3,duplicates=True))[0]['count'],7)
    def test_repeated_frames_emit_one_record(self):self.assertEqual(len(self.run_scene(scene())),1)
    def test_more_than_ten_is_not_clamped(self):
        ds=scene(10,0);ds.append(dict(class_id=0,bbox=[238,43,257,61],confidence=.9))
        self.assertIsNone(self.run_scene(ds)[0]['count'])
    def test_stock_removal_does_not_rewrite_arrival(self):
        c=ArrivalCounter()
        for i in range(4):c.step(i*.08,scene(10,0),i)
        for i in range(4,8):c.step(i*.08,scene(6,4),i)
        self.assertEqual(c.finish()[0]['count'],10)
    def test_new_loaded_tray_after_empty_rearms(self):
        c=ArrivalCounter()
        for i in range(4):c.step(i*.08,scene(7,3),i)
        for i in range(4,10):c.step(i*.08,scene(0,10),i)
        for i in range(10,15):c.step(i*.08,scene(9,1),i)
        self.assertEqual([r['count'] for r in c.finish()],[7,9])
if __name__=='__main__':unittest.main(verbosity=2)
