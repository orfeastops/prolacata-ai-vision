import unittest
import numpy as np
from run_room11_storage import TankLinker, PresenceCounter, PAYLOAD_CONFIG


class IntegrationRules(unittest.TestCase):
    def test_station_placement_follows_same_tank_to_exit_once(self):
        c=TankLinker();c.step(0,[np.array([.43,.75,.59,.99])])
        self.assertEqual(c.placement({'destination_xy':[160,190]},0),1)
        for n in range(1,31):
            dy=n*.019
            c.step(n*.1,[np.array([.43,.75-dy,.59,.99-dy])])
        self.assertEqual(len(c.exits),1)
        self.assertEqual(c.exits[0]['status'],'storage_proposal')

    def test_gap_does_not_transfer_fill_to_new_tank(self):
        c=TankLinker();c.step(0,[np.array([.43,.75,.59,.99])])
        c.placement({'destination_xy':[160,190]},0)
        for n in range(31):
            dy=n*.019;c.step(3+n*.1,[np.array([.43,.75-dy,.59,.99-dy])])
        self.assertEqual(c.exits[0]['status'],'exit_without_linked_placement')

    def test_ambiguous_destination_not_assigned(self):
        c=TankLinker();c.step(0,[np.array([.40,.72,.52,.92]),np.array([.48,.80,.62,1.])])
        self.assertIsNone(c.placement({'destination_xy':[160,190]},0))
        self.assertEqual(len(c.unlinked),1)

    def test_duplicate_boxes_do_not_create_two_tanks(self):
        c=TankLinker();b=np.array([.43,.75,.59,.99]);c.step(0,[b,b.copy()])
        self.assertEqual(len(c.tracks),1)
        self.assertEqual(c.placement({'destination_xy':[160,190]},0),1)

    def test_station_episode_consumed_once_after_detection_occlusion(self):
        c=TankLinker();b=np.array([.43,.75,.59,.99]);c.step(0,[b])
        c.placement({'destination_xy':[160,190]},0)
        # Frames continue, but detector misses the covered tank for two seconds.
        for n in range(1,21):c.step(n*.1,[])
        for n in range(31):
            dy=n*.019;c.step(2.1+n*.1,[b-np.array([0,dy,0,dy])])
        self.assertEqual(c.exits[0]['status'],'storage_proposal')
        self.assertEqual(c.exits[0]['association'],'filling_station_episode_to_outbound_trajectory')
        for n in range(31):
            dy=n*.019;c.step(5.2+n*.1,[b-np.array([0,dy,0,dy])])
        self.assertEqual(c.exits[1]['status'],'exit_without_linked_placement')

    def test_old_station_episode_expires(self):
        c=TankLinker();b=np.array([.43,.75,.59,.99]);c.step(0,[b])
        c.placement({'destination_xy':[160,190]},0)
        for n in range(1,620):c.step(n*.1,[])
        for n in range(31):
            dy=n*.019;c.step(62+n*.1,[b-np.array([0,dy,0,dy])])
        self.assertEqual(c.exits[0]['status'],'exit_without_linked_placement')

    def test_motion_into_tank_accepted_without_quantity_estimation(self):
        c=PresenceCounter(dict(PAYLOAD_CONFIG))
        for n in range(20):
            x=350-130*n/19;y=250-60*n/19
            c.step(n*.1,[dict(bbox=[x-20,y-15,x+20,y+15],confidence=.9,quantity=1)])
        c.step(2.5,[])
        self.assertEqual(len(c.events),1)
        self.assertIn('destination_xy',c.events[0])


if __name__=='__main__':unittest.main()
