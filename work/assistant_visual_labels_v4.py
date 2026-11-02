"""Assistant-authored visual observations, not a trained-counter prediction.

The values below were authored after inspecting the referenced original-frame
contact sheets. Rendering/exporting this file does not perform visual inference.
Time intervals express observation uncertainty, not exact release timestamps.
"""

def transfer(side, quantity, pickup, deposit, note='', confidence='high'):
    return dict(action='whole_block_transfer', side=side, quantity=quantity,
                pickup_interval_s=pickup, deposit_interval_s=deposit,
                quantity_confidence=confidence, note=note)

def negative(side, interval, action, note):
    return dict(action=action, side=side, interval_s=interval,
                quantity=0, quantity_confidence='high', note=note)

def uncertain(side, interval, note):
    return dict(action='unresolved_material_or_boundary', side=side,
                interval_s=interval, quantity=None,
                quantity_confidence='unresolved', note=note)

CLIPS = {
 'C03': [
    negative('left', [0, 1.4], 'arrange_existing_cheese', 'Pre-roll shows the preceding deposit before the start; initial movements arrange existing cheese.'),
    uncertain('right', [1.5, 10.5], 'Material is removed from an apparently emptied tray, followed by reaching below the conveyor. A small white object is carried over the filling tank at approximately 6.5-7.5 s. Its origin and identity are occluded; do not force either zero or one whole block.'),
    negative('left', [3, 11.5], 'empty_hand_motion', 'Gestures and waiting; no observed new whole-block pickup.'),
    negative('right', [10.5, 12.5], 'scrap_destination_motion', 'Material is taken to the upper-right scrap tank, not the filling tank.'),
    transfer('left', 2, [12.6, 13.2], [13.4, 14.4], 'Two raised tray blocks lifted and carried together; tray cells become exposed.'),
    transfer('right', 2, [13.8, 14.4], [14.8, 15.6], 'Two adjacent tray blocks carried toward the filling tank; subsequent arranging is not a new addition.'),
    transfer('left', 2, [16.0, 16.8], [16.8, 18.6], 'Two blocks carried with separate hands; placements are staggered within the interval.'),
    transfer('right', 2, [19.0, 19.6], [20.0, 20.6], 'Two blocks lifted together and released into the tank.'),
    transfer('left', 1, [22.2, 22.8], [23.2, 24.4], 'One remaining block is visible in this carry; no fixed two-per-motion rule.'),
    transfer('right', 1, [22.4, 22.8], [23.4, 24.0], 'One block is lifted in one hand; the other hand remains empty.'),
    negative('right', [25.0, 28.4], 'tray_reposition', 'Empty tray is pushed away and the next loaded tray is moved into position.'),
    transfer('left', 2, [29.2, 29.8], [30.2, 31.0], 'Context after the original clip shows the deposit; exclude these two from the original 0-29.96 s interval.'),
    transfer('right', 2, [29.4, 30.0], [30.6, 31.4], 'Context after the original clip shows the deposit; exclude these two from the original interval.'),
 ],
 'C04': [
    transfer('left', 2, [-0.8, -0.2], [0.2, 1.0], 'Pickup begins before the original clip. Pre-roll shows one rectangular block per hand; deposit is inside the clip.'),
    negative('right', [0, 1], 'scrap_destination_motion', 'Clearing material toward the scrap area; no whole block deposited into the filling tank.'),
    transfer('left', 2, [2.4, 3.2], [3.5, 4.5], 'One separate whole block in each hand.'),
    transfer('right', 2, [3.6, 4.6], [5.0, 5.8], 'Two blocks carried separately and placed in the filling tank.'),
    negative('left', [5.0, 6.8], 'empty_hand_or_residue_motion', 'Touching/scraping the emptied tray and hand motion; no raised whole block is lifted.'),
    negative('right', [6.4, 8.0], 'tray_reposition', 'Moves the empty tray along the conveyor.'),
    transfer('left', 2, [10.8, 11.6], [11.8, 12.6], 'Two visible blocks leave the loaded tray.'),
    transfer('left', 2, [14.0, 14.8], [15.2, 16.0], 'Two visible blocks are carried together.'),
    negative('right', [12.0, 17.2], 'empty_hand_motion', 'Repeated gestures near face/chest while the left side transfers cheese.'),
    transfer('left', 2, [17.2, 18.0], [18.2, 19.0], 'Two visible blocks lifted and deposited.'),
    negative('right', [17.4, 19.6], 'touch_without_pickup', 'Touches the cheese/tray then withdraws and gestures with empty hands. Contact alone must not increment the count.'),
    transfer('right', 2, [20.0, 21.0], [21.4, 22.6], 'Two separate blocks, one in each hand, are taken to the tank.'),
    transfer('left', 2, [22.6, 23.2], [23.4, 24.2], 'Two remaining blocks lifted together.'),
    negative('left', [24.4, 25.6], 'arrange_existing_cheese', 'Repositions blocks already inside the tank without another pickup.'),
    negative('right', [24.0, 28.0], 'tray_reposition', 'Pushes empty tray away and helps position the next loaded tray.'),
    transfer('left', 2, [28.4, 29.0], [29.4, 29.8], 'Both deposit and pickup are inside the original clip.'),
    transfer('right', 2, [29.2, 29.8], [30.2, 31.2], 'Pickup is inside the original clip, deposit is after its end; exclude from the original-clip addition count.'),
 ],
 'C05': [
    transfer('left', 2, [-1.8, -1.0], [-0.6, -0.12], 'Pre-roll-only transfer. Both blocks appear deposited before t=0; excluded from the original-clip sum.'),
    transfer('right', 2, [-1.2, -0.6], [0.2, 1.6], 'Pickup is before the clip; two separately held blocks are deposited after the start.'),
    transfer('left', 2, [1.2, 1.8], [2.2, 3.6], 'One block per hand; placing and subsequent arranging overlap in time.'),
    transfer('right', 2, [3.0, 4.0], [4.2, 5.4], 'One block per hand carried from tray to filling tank.'),
    negative('left', [3.6, 6.6], 'arrange_existing_cheese', 'Repositions the blocks already deposited without another tray pickup.'),
    transfer('right', 2, [6.4, 7.4], [7.8, 8.6], 'Two visible remaining tray blocks taken to the filling tank.'),
    negative('left', [7.2, 11.4], 'tray_reposition', 'Moves the emptied tray past the filling station.'),
    negative('right', [8.8, 12.2], 'salt_or_bucket_material', 'Turns to the white bucket, then sprinkles/spreads its contents over the layer; no whole-block pickup.'),
    negative('left', [14.0, 16.4], 'separator_sheet', 'Brings a large thin white separator sheet from the left and spreads it over the cheese layer.'),
    transfer('right', 2, [15.0, 16.0], [16.4, 17.6], 'Two raised blocks, separately visible in the hands.'),
    transfer('left', 2, [17.0, 17.6], [17.6, 18.4], 'Two blocks lifted together from the near end of the tray.'),
    transfer('right', 2, [18.4, 19.2], [19.6, 20.4], 'Two visible blocks carried toward the tank.'),
    transfer('left', 2, [19.0, 19.6], [19.8, 20.6], 'Two blocks lifted, carried and deposited.'),
    transfer('left', 2, [21.2, 22.0], [22.2, 23.4], 'Two remaining blocks carried with separate hands.'),
    negative('right', [22.0, 24.2], 'empty_hand_or_residue_motion', 'Sweeps/touches the emptied tray; no raised whole block lifted.'),
    negative('right', [24.2, 26.0], 'tray_reposition', 'Pushes the emptied tray away.'),
    negative('left', [25.2, 29.9], 'empty_hand_motion', 'Repeated empty-hand gestures above the tank, no cheese pickup.'),
 ],
 'C06': [
    transfer('left', 2, [-1.0, -0.6], [-0.08, 0.2], 'Deposit straddles the original clip start and is partly hidden by the arm/rim. Carry quantity is two; attribution of 0, 1 or 2 to the original clip remains unresolved.', confidence='medium'),
    transfer('right', 2, [-0.08, 0.6], [1.0, 2.2], 'Two separate blocks are carried from the tray into the tank.'),
    transfer('left', 2, [1.4, 2.0], [2.2, 3.0], 'Two raised remaining blocks lifted, one per hand.'),
    negative('right', [3.0, 5.2], 'tray_reposition', 'Moves the emptied tray away and positions the next loaded tray.'),
    transfer('left', 2, [5.4, 6.0], [6.4, 7.2], 'Two whole blocks lifted together.'),
    transfer('right', 2, [5.8, 6.6], [6.8, 7.8], 'Two separate blocks, one per hand.'),
    transfer('left', 2, [8.0, 8.6], [8.8, 9.6], 'Two raised blocks lifted from adjacent tray cells.'),
    transfer('right', 2, [8.6, 9.4], [10.0, 10.8], 'Two separately visible blocks carried together.'),
    transfer('left', 2, [11.0, 11.6], [12.0, 13.2], 'Two remaining blocks carried in separate hands.'),
    negative('right', [12.0, 14.8], 'tray_reposition', 'Pushes the empty tray away and brings in the loaded tray.'),
    negative('left', [13.2, 14.8], 'arrange_existing_cheese', 'Repositions cheese already inside the tank.'),
    transfer('right', 2, [15.0, 16.0], [16.4, 17.8], 'Two clearly separate blocks, one per hand.'),
    transfer('left', 2, [15.6, 16.2], [16.8, 18.0], 'Two blocks lifted together and lowered into the tank.'),
    transfer('right', 2, [18.6, 19.6], [19.8, 20.6], 'Two separately held whole blocks deposited.'),
    transfer('left', 2, [19.0, 19.6], [19.8, 20.8], 'Two blocks lifted together, then lowered into the tank.'),
    transfer('left', 2, [21.4, 22.0], [22.4, 23.4], 'Two remaining blocks deposited while the opposite side obtains salt.'),
    negative('right', [21.0, 24.0], 'salt_or_bucket_material', 'Takes material from the white bucket and scatters it across the layer, with no whole-block pickup.'),
    negative('right', [24.6, 29.9], 'tray_and_residue_handling', 'Moves/scrapes the emptied tray and turns toward the scrap tank; no filling-tank whole-block transfer.'),
    negative('left', [26.8, 29.9], 'separator_sheet', 'Brings a large white sheet from off-screen left and lays it over the layer.'),
 ],
}
