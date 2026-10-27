import unittest
from block_transfer_counter import BlockCounter, Pickup, Release

def pickup(ids=('a','b','c'), eid='p', t=1):
    return Pickup(eid,'tray',ids,t,verified=True)

def release(ids, eid='r', t=2, **kw):
    args=dict(event_id=eid,block_ids=ids,time_s=t,destination='filling_tank',tank_id='A',verified=True)
    args.update(kw)
    return Release(**args)

class BlockTests(unittest.TestCase):
    def test_three_blocks_in_one_motion(self):
        c=BlockCounter();c.pickup(pickup())
        self.assertEqual(c.release(release(('a','b','c'))),3)
        self.assertEqual(c.report()['observed_additions_by_tank'],{'A':3})

    def test_staggered_release_keeps_other_block(self):
        c=BlockCounter();c.pickup(pickup(('a','b')))
        c.release(release(('a',),'r1'))
        self.assertEqual(c.report()['still_carried_block_ids'],['b'])
        c.release(release(('b',),'r2',3))
        self.assertEqual(c.report()['observed_additions_by_tank'],{'A':2})

    def test_two_hands_same_block_and_repeated_frames(self):
        c=BlockCounter();c.pickup(pickup(('a',),'left'));c.pickup(pickup(('a',),'right'))
        c.release(release(('a',),'left_release'))
        c.release(release(('a',),'right_release'))
        c.release(release(('a',),'right_release'))
        self.assertEqual(c.report()['observed_additions_by_tank'],{'A':1})

    def test_unknown_is_pending_not_one(self):
        c=BlockCounter();c.pickup(pickup(None))
        self.assertEqual(c.release(release(None)),0)
        self.assertEqual(c.report()['observed_additions_by_tank'],{})
        self.assertIn('r',c.report()['unresolved'])

    def test_crumbs_after_cheese_do_not_add_or_cancel(self):
        c=BlockCounter();c.pickup(pickup(('a',)));c.release(release(('a',)))
        c.release(release(None,'crumb',3,material='crumbs',destination='crumb_tank'))
        self.assertEqual(c.report()['observed_additions_by_tank'],{'A':1})

    def test_mixed_unknown_batch_does_not_partially_commit(self):
        c=BlockCounter();c.pickup(pickup(('a',)))
        c.release(release(('a','b')))
        self.assertEqual(c.report()['observed_additions_by_tank'],{})
        self.assertEqual(c.report()['still_carried_block_ids'],['a'])

    def test_release_before_evidence_can_be_retried(self):
        c=BlockCounter();r=release(('a',));c.release(r);c.pickup(pickup(('a',)))
        self.assertEqual(c.release(r),1)
        self.assertNotIn('r',c.report()['unresolved'])

    def test_return_to_tray_requires_new_pickup(self):
        c=BlockCounter();c.pickup(pickup(('a',)))
        c.release(release(('a',),'return',2,destination='conveyor_return'))
        c.release(release(('a',),'missing',3))
        self.assertEqual(c.report()['observed_additions_by_tank'],{})
        c.pickup(pickup(('a',),'repick',2.5));c.release(release(('a',),'missing',3))
        self.assertEqual(c.report()['observed_additions_by_tank'],{'A':1})

    def test_unknown_observation_can_be_resolved_without_new_id(self):
        c=BlockCounter();c.pickup(pickup(None));c.release(release(None))
        c.pickup(pickup(('a','b','c')));c.release(release(('a','b','c')))
        self.assertEqual(c.report()['observed_additions_by_tank'],{'A':3})
        self.assertFalse(c.report()['unresolved'])

    def test_conflicting_tank_no_partial_change(self):
        c=BlockCounter();c.pickup(pickup(('a','b')));c.release(release(('a',)))
        with self.assertRaises(ValueError):c.release(release(('b','a'),'bad',3,tank_id='B'))
        self.assertEqual(c.report()['observed_additions_by_tank'],{'A':1})
        self.assertEqual(c.report()['still_carried_block_ids'],['b'])

    def test_no_quantity_from_empty_tray_or_gloves(self):
        c=BlockCounter()
        c.release(release(None,'tray',material='empty_tray',destination='conveyor_return'))
        c.release(release(None,'glove',material='glove',verified=False))
        self.assertEqual(c.report()['observed_additions_by_tank'],{})
        self.assertEqual(c.report()['excluded_events'],1)

    def test_no_fixed_tray_capacity(self):
        c=BlockCounter();ids=tuple(str(i) for i in range(11));c.pickup(pickup(ids));c.release(release(ids))
        self.assertEqual(c.report()['observed_additions_by_tank'],{'A':11})

    def test_user_seven_block_scenario_bookkeeping_only(self):
        c=BlockCounter()
        c.pickup(pickup(('l1','l2','r1','r2'),'first',2))
        c.release(release(('l1','l2','r1','r2'),'first_release',4))
        c.pickup(pickup(('l3','l4','r3'),'second',5.5))
        for bid,eid,t in [('l3','L1',7.1),('r3','R',7.94),('l4','L2',8.88)]:
            c.release(release((bid,),eid,t))
        self.assertEqual(c.report()['observed_additions_by_tank'],{'A':7})
        self.assertFalse(c.report()['count_complete'])

if __name__=='__main__':unittest.main()
