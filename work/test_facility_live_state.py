import importlib.util,pathlib,tempfile,unittest
path=pathlib.Path('outputs/facility_dataset/temporal_pipeline/live_state.py')
spec=importlib.util.spec_from_file_location('live_state',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
T='2026-10-21T08:00:00+00:00'
class LiveTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=pathlib.Path(self.tmp.name)/'state.sqlite';self.state=module.LiveState(self.path);self.state.start_tank('A',T,True)
    def tearDown(self):self.state.close();self.tmp.cleanup()
    def add(self,eid='release1',tank='A',quantity=1,**kw):
        args=dict(event_id=eid,tank_id=tank,quantity=quantity,object_kind='whole_cheese_block',destination='filling_tank',captured_at=T,validated=True);args.update(kw);return self.state.placement(**args)
    def test_overlap_and_restart_do_not_double_count(self):
        self.add();self.add();self.state.close();self.state=module.LiveState(self.path);self.add()
        self.assertEqual(self.state.report('A')['confirmed_blocks'],1)
    def test_start_same_tank_again_does_not_reset(self):
        self.add(quantity=3);self.state.start_tank('A',T);self.assertEqual(self.state.report('A')['confirmed_blocks'],3)
    def test_second_tank_keeps_first_count(self):
        self.add(quantity=3);self.state.start_tank('B',T,True);self.add('release2','B',1)
        self.assertEqual(self.state.report('A')['confirmed_blocks'],3);self.assertEqual(self.state.report('B')['confirmed_blocks'],1)
    def test_pending_quantity_requires_validation(self):
        self.add(quantity=None,validated=False);self.assertEqual(self.state.report('A')['confirmed_blocks'],0)
        self.add(quantity=1);self.assertEqual(self.state.report('A')['confirmed_blocks'],1)
    def test_crumbs_and_separator_do_not_add(self):
        self.add(object_kind='crumbs',destination='crumb_tank');self.add('sep',object_kind='separator',destination='separator_rack')
        self.assertEqual(self.state.report('A')['confirmed_blocks'],0)
    def test_frame_gap_preserves_count_and_marks_coverage(self):
        self.add(quantity=3);self.state.record_gap('lost_frames',T,'2026-10-21T08:00:05+00:00')
        self.assertEqual(self.state.report('A')['confirmed_blocks'],3);self.assertFalse(self.state.report('A')['count_complete'])
        with self.assertRaises(ValueError):self.state.certify_coverage('A')
    def test_unverified_camera15_match_not_reported_as_storage(self):
        self.state.transition('stored','A','stored_camera15',T,False)
        self.assertNotIn('stored_camera15',self.state.report('A')['validated_transition_times'])
        self.state.transition('stored','A','stored_camera15',T,True)
        self.assertIn('stored_camera15',self.state.report('A')['validated_transition_times'])
    def test_odd_exact_total_without_standard_capacity(self):
        self.add(quantity=3);self.state.certify_coverage('A');self.state.transition('out','A','departed_camera11',T,True)
        self.assertEqual(self.state.report('A')['exact_block_total'],3)
    def test_conflicting_final_event_rejected(self):
        self.add()
        with self.assertRaises(ValueError):self.add(quantity=2)
        self.assertEqual(self.state.report('A')['confirmed_blocks'],1)
    def test_timestamps_require_explicit_time_zone(self):
        with self.assertRaises(ValueError):self.state.start_tank('B','2026-10-21T11:00:00')
    def test_unknown_initial_tank_never_declared_complete(self):
        self.state.start_tank('B',T,False);self.add('b','B',3);self.state.certify_coverage('B');self.state.transition('out','B','departed_camera11',T,True)
        self.assertIsNone(self.state.report('B')['exact_block_total'])
if __name__=='__main__':unittest.main()
