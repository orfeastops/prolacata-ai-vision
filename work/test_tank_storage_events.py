import unittest
from tank_storage_events import StorageCounter


class StorageRuleTests(unittest.TestCase):
    def fill(self, counter, episode='a', **kwargs):
        counter.observe_filling(episode, '2026-10-25T08:00:00+02:00', 'fill-frame',
                                cheese_placed=kwargs.get('cheese', True),
                                designated_station_workers=kwargs.get('workers', True))

    def exit(self, counter, episode='a', direction='outbound'):
        return counter.observe_crossing(episode, '2026-10-25T08:01:00+02:00',
                                        'exit-frame', room=11, direction=direction)

    def test_filling_then_exit_counts_once_without_amount(self):
        c = StorageCounter(); self.fill(c)
        self.assertIsNotNone(self.exit(c)); self.assertIsNone(self.exit(c))
        self.assertEqual(c.user_records(), [{'event': 'tank_storage',
                         'exited_at': '2026-10-25T08:01:00+02:00'}])

    def test_empty_or_wrong_workers_do_not_count(self):
        for options in ({'cheese': False}, {'workers': False}):
            c = StorageCounter(); self.fill(c, **options)
            self.assertIsNone(self.exit(c))

    def test_internal_or_inbound_movement_does_not_count(self):
        c = StorageCounter(); self.fill(c)
        self.assertIsNone(self.exit(c, direction='inbound'))
        self.assertIsNotNone(self.exit(c))

    def test_other_tank_and_broken_association_do_not_inherit_filling(self):
        c = StorageCounter(); self.fill(c)
        self.assertIsNone(self.exit(c, episode='b'))
        c.lose_continuity('a'); self.assertIsNone(self.exit(c))

    def test_clock_without_offset_rejected(self):
        with self.assertRaises(ValueError):
            StorageCounter().observe_crossing('a', '2026-10-25T08:01:00',
                                              'frame', room=11, direction='outbound')


if __name__ == '__main__':
    unittest.main()
