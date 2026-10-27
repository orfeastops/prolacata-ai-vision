import importlib.util,pathlib,sys,unittest
p=pathlib.Path('outputs/facility_dataset/temporal_pipeline/event_counter.py')
s=importlib.util.spec_from_file_location('facility_event_counter',p);m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m)

def event(id,hand='left',worker='worker1',**kw):
    fields=dict(event_id=id,worker_track=worker,hand_track=hand,tray_cycle_id='tray1',tank_id='tank1',
                picked_quantity=1,pickup_object='whole_cheese_block',release_object='whole_cheese_block',
                destination='filling_tank',pickup_observed=True,release_observed=True,release_relative_s=5.7,
                quantity_basis='visually_reviewed');fields.update(kw);return m.HandTransfer(**fields)

class CounterTests(unittest.TestCase):
    def test_separate_pickups_waiting_for_empty_tank_do_not_add_until_release(self):
        ledger=m.ProductionLedger()
        early=event('early','early_pickup_hand',release_observed=False,release_relative_s=None,pickup_episode_id='B022')
        late=event('late','late_pickup_hand',release_observed=False,release_relative_s=None,pickup_episode_id='B022')
        ledger.ingest(early);ledger.ingest(late)
        self.assertEqual(ledger.report()['confirmed_blocks_by_tank'],{})
        ledger.ingest(m.replace(early,release_observed=True,release_relative_s=13.5))
        self.assertEqual(ledger.report()['confirmed_blocks_by_tank'],{'tank1':1})
        ledger.ingest(m.replace(late,release_observed=True,release_relative_s=13.75))
        self.assertEqual(ledger.report()['confirmed_blocks_by_tank'],{'tank1':2})
    def test_actual_odd_total_is_retained_without_a_standard_tank_quantity(self):
        ledger=m.ProductionLedger()
        for i in range(3):ledger.ingest(event(str(i),pickup_episode_id='individual_'+str(i)))
        self.assertEqual(ledger.report()['confirmed_blocks_by_tank'],{'tank1':3})
    def test_simultaneous_four_hands(self):
        ledger=m.ProductionLedger()
        for worker in ('a','b'):
            for hand in ('left','right'):ledger.ingest(event(worker+hand,hand,worker))
        self.assertEqual(ledger.report()['confirmed_blocks_by_tank'],{'tank1':4})
        self.assertTrue(ledger.corroborate_tray('tray1',4)['consistent'])
    def test_one_cheese_one_crumb(self):
        ledger=m.ProductionLedger();ledger.ingest(event('cheese'));ledger.ingest(event('crumb',hand='right',picked_quantity=0,pickup_object='crumbs',release_object='crumbs',destination='crumb_tank'))
        self.assertEqual(ledger.report()['confirmed_blocks_by_tank'],{'tank1':1})
        self.assertEqual(len(ledger.excluded),1)
        self.assertTrue(ledger.corroborate_tray('tray1',1)['consistent'])
    def test_pickup_is_not_a_placement(self):
        ledger=m.ProductionLedger();ledger.ingest(event('a',release_observed=False,release_relative_s=None))
        self.assertFalse(ledger.report()['confirmed_blocks_by_tank']);self.assertIn('a',ledger.pending)
        ledger.ingest(event('a'));self.assertEqual(ledger.report()['confirmed_blocks_by_tank'],{'tank1':1})
    def test_duplicate_and_height_evidence_not_double_counted(self):
        ledger=m.ProductionLedger();e=event('a');ledger.ingest(e);ledger.ingest(e)
        self.assertEqual(ledger.corroborate_tray('tray1',1)['production_added_by_tray_check'],0)
        self.assertEqual(ledger.report()['confirmed_blocks_by_tank'],{'tank1':1})
    def test_occluded_slot_unknown_and_inconsistent_tray(self):
        ledger=m.ProductionLedger();ledger.ingest(event('a'))
        self.assertIsNone(ledger.corroborate_tray('tray1',None)['consistent'])
        self.assertFalse(ledger.corroborate_tray('tray1',2)['consistent'])
        self.assertEqual(ledger.report()['confirmed_blocks_by_tank'],{'tank1':1})
    def test_separator_and_unknown_quantity(self):
        ledger=m.ProductionLedger();ledger.ingest(event('separator',pickup_object='separator',release_object='separator',destination='separator_rack'))
        ledger.ingest(event('unknown',picked_quantity=None,quantity_basis='unknown'))
        self.assertFalse(ledger.report()['confirmed_blocks_by_tank']);self.assertIn('unknown',ledger.pending)
    def test_return_to_tray_and_changed_final_event(self):
        ledger=m.ProductionLedger();ledger.ingest(event('return',destination='conveyor_return'))
        self.assertFalse(ledger.report()['confirmed_blocks_by_tank'])
        ledger.ingest(event('a'));ledger.ingest(event('a',picked_quantity=2));self.assertEqual(len(ledger.conflicts),1)
    def test_one_physical_tray_and_separate_pickup_episodes(self):
        ledger=m.ProductionLedger()
        for episode in ('first','second'):
            for hand in ('left','right'):ledger.ingest(event(episode+hand,hand,pickup_episode_id=episode))
        self.assertTrue(ledger.corroborate_tray('tray1',2,pickup_episode_ids=['first'])['consistent'])
        self.assertTrue(ledger.corroborate_tray('tray1',4)['consistent'])
    def test_new_frame_event_id_for_same_hand_episode_is_not_a_new_block(self):
        ledger=m.ProductionLedger();ledger.ingest(event('frame1',pickup_episode_id='same_pickup'))
        ledger.ingest(event('frame2',pickup_episode_id='same_pickup'))
        self.assertEqual(ledger.report()['confirmed_blocks_by_tank'],{'tank1':1})
    def test_invalid_fractional_and_negative_quantities(self):
        for quantity in (-1,1.5,True):
            with self.assertRaises(ValueError):m.ProductionLedger().ingest(event('bad',picked_quantity=quantity))

if __name__=='__main__':unittest.main()
