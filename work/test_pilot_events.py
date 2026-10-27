import importlib.util, pathlib, unittest
spec = importlib.util.spec_from_file_location('counter', pathlib.Path('outputs/feta_pilot/count_events.py'))
counter = importlib.util.module_from_spec(spec); spec.loader.exec_module(counter)

def event(eid, worker='A', hand='L', destination='production', blocks=1, start=1, end=2, status='confirmed'):
    return dict(event_id=eid,worker=worker,hand=hand,destination=destination,blocks=blocks,start_seconds=start,end_seconds=end,status=status,tank_id='T01')

def data(events):
    return dict(schema_version=1,source=dict(segment_duration_seconds=60),events=events)

class CountingTests(unittest.TestCase):
    def test_four_hands(self):
        report=counter.aggregate(data([event(w+h,worker=w,hand=h) for w in 'AB' for h in 'LR']))
        self.assertEqual(report['tanks']['T01']['confirmed_blocks'],4)
    def test_one_cheese_one_crumb(self):
        report=counter.aggregate(data([event('1'),event('2',hand='R',destination='crumb',blocks=0)]))
        self.assertEqual(report['tanks']['T01']['confirmed_blocks'],1)
        self.assertEqual(report['tanks']['T01']['crumb_disposals'],1)
    def test_unknown_is_not_assumed_cheese(self):
        report=counter.aggregate(data([event('1',destination='unknown',blocks=None,status='needs_review')]))
        self.assertEqual(report['tanks']['T01']['confirmed_blocks'],0)
        self.assertEqual(report['tanks']['T01']['unresolved_actions'],1)
        self.assertFalse(report['full_tank_totals_available'])
    def test_duplicate_rejected(self):
        with self.assertRaises(ValueError):counter.aggregate(data([event('1'),event('1')]))
    def test_same_hand_overlap_rejected(self):
        with self.assertRaises(ValueError):counter.aggregate(data([event('1'),event('2')]))
    def test_unidentified_hand_overlap_rejected(self):
        with self.assertRaises(ValueError):counter.aggregate(data([event('1'),event('2',hand='U')]))
    def test_sequential_actions_allowed(self):
        report=counter.aggregate(data([event('1'),event('2',start=2,end=3)]))
        self.assertEqual(report['tanks']['T01']['confirmed_blocks'],2)
    def test_separator_is_not_cheese(self):
        report=counter.aggregate(data([event('1',destination='separator',blocks=0)]))
        self.assertEqual(report['tanks']['T01']['confirmed_blocks'],0)

unittest.main()
