"""Object-level counting, independent of worker identity and number of hands.

This is an evidence consumer, NOT an image detector. Stable block IDs and
validated pickup/release observations must come from an object tracker/review.
Unknown quantities are pending; hand-cycle proposals cannot create block IDs.
"""
from dataclasses import dataclass, field
import math


@dataclass(frozen=True)
class Pickup:
    event_id: str
    tray_id: str
    block_ids: tuple[str, ...] | None
    time_s: float
    material: str = 'whole_cheese_block'
    verified: bool = False


@dataclass(frozen=True)
class Release:
    event_id: str
    block_ids: tuple[str, ...] | None
    time_s: float
    destination: str
    tank_id: str | None = None
    material: str = 'whole_cheese_block'
    verified: bool = False


@dataclass
class BlockCounter:
    pickups: dict = field(default_factory=dict)
    releases: dict = field(default_factory=dict)
    carried: dict = field(default_factory=dict)
    consumed: dict = field(default_factory=dict)
    accepted: dict = field(default_factory=dict)
    pending: dict = field(default_factory=dict)
    excluded: dict = field(default_factory=dict)

    @staticmethod
    def validate(event):
        if not event.event_id or not math.isfinite(event.time_s) or event.time_s < 0:
            raise ValueError('Stable event ID and finite non-negative time required')
        if event.block_ids is not None:
            if not isinstance(event.block_ids, tuple) or not event.block_ids:
                raise ValueError('Block IDs must be a nonempty tuple or unknown')
            if any(not isinstance(b, str) or not b for b in event.block_ids):
                raise ValueError('Nonempty physical block IDs required')
            if len(set(event.block_ids)) != len(event.block_ids):
                raise ValueError('Duplicate physical block within one observation')

    def pickup(self, event: Pickup):
        self.validate(event)
        if not event.tray_id:
            raise ValueError('Tracked tray identity required')
        old = self.pickups.get(event.event_id)
        if old is not None and old != event:
            if ('pickup:'+event.event_id not in self.pending
                    or old.tray_id != event.tray_id or old.time_s != event.time_s):
                raise ValueError('Conflicting pickup evidence; review required')
        if old == event:
            return
        # Validate the entire observation before changing any state.
        if event.verified and event.material == 'whole_cheese_block' and event.block_ids:
            for block in event.block_ids:
                if block in self.consumed:
                    raise ValueError('Block already released; identity cannot be reused')
                previous = self.carried.get(block)
                if previous and (previous.tray_id != event.tray_id or previous.time_s != event.time_s):
                    raise ValueError('Conflicting physical pickup for same block')
        self.pickups[event.event_id] = event
        if event.verified and event.material == 'whole_cheese_block' and event.block_ids:
            for block in event.block_ids:
                self.carried.setdefault(block, event)
            self.pending.pop('pickup:'+event.event_id, None)
        else:
            self.pending['pickup:'+event.event_id] = 'Unverified object identity, material or quantity'

    def release(self, event: Release):
        self.validate(event)
        old = self.releases.get(event.event_id)
        if old is not None:
            if old != event:
                if (event.event_id not in self.pending or old.time_s != event.time_s
                        or old.tank_id != event.tank_id or old.destination != event.destination):
                    raise ValueError('Conflicting release evidence; review required')
            if event.event_id not in self.pending:
                return 0
        if event.verified and (event.material in {'crumbs','salt','separator','empty_tray'}
                or event.destination in {'crumb_tank','conveyor_return','separator_rack'}):
            # Do not cancel a different whole-block release by the same hand.
            if event.material == 'whole_cheese_block' and event.block_ids:
                if any(b in self.consumed for b in event.block_ids):
                    raise ValueError('Cannot return a block already counted in a tank')
                for block in event.block_ids:
                    self.carried.pop(block, None)
            self.releases[event.event_id] = event
            self.excluded[event.event_id] = event
            self.pending.pop(event.event_id, None)
            return 0
        if not (event.verified and event.material == 'whole_cheese_block'
                and event.destination == 'filling_tank' and event.tank_id and event.block_ids):
            self.releases[event.event_id] = event
            self.pending[event.event_id] = 'Whole-block release quantity or destination unverified'
            return 0
        fresh = []
        for block in event.block_ids:
            previous = self.consumed.get(block)
            if previous:
                if previous.tank_id != event.tank_id:
                    raise ValueError('Same block assigned to different tanks')
                continue  # Two hands or repeated frames observing one physical block.
            pickup = self.carried.get(block)
            if pickup is None or pickup.time_s > event.time_s:
                self.releases[event.event_id] = event
                self.pending[event.event_id] = 'Continuous pickup evidence missing'
                return 0
            fresh.append(block)
        self.releases[event.event_id] = event
        self.pending.pop(event.event_id, None)
        for block in fresh:
            self.consumed[block] = event
            self.carried.pop(block)
        self.accepted[event.event_id] = {'event':event, 'new_block_ids':tuple(fresh)}
        return len(fresh)

    def report(self):
        tanks = {}
        for event in self.consumed.values():
            tanks[event.tank_id] = tanks.get(event.tank_id, 0) + 1
        return dict(observed_additions_by_tank=tanks, still_carried_block_ids=sorted(self.carried),
            unresolved=dict(self.pending), excluded_events=len(self.excluded),
            count_complete=False, scope='Supplied object evidence only; not verified video production')
