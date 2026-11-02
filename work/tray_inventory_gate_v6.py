"""Conservation gate for future inventory + load observations.

This is bookkeeping, NOT an image inventory detector. Missing/occluded source
evidence never becomes zero and can never authorize a confirmed placement.
"""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class InventoryObservation:
    observation_id: str
    tray_id: str
    time_s: float
    count: int | None
    fully_visible: bool
    aligned: bool
    provenance: str


class InventoryGate:
    def __init__(self):
        self.observations = {}; self.windows = {}; self.claims = {}; self.releases = {}

    def observe(self, observation):
        o = observation
        if not o.observation_id or not o.tray_id or not o.provenance or not math.isfinite(o.time_s):
            raise ValueError('Traceable finite inventory observation required')
        if o.count is not None and (type(o.count) is not int or o.count < 0):
            raise ValueError('Count must be a nonnegative integer or None')
        prior = self.observations.get(o.observation_id)
        if prior is not None and prior != o: raise ValueError('Conflicting frozen observation')
        self.observations[o.observation_id] = o

    def window(self, before_id, after_id):
        key = (before_id, after_id)
        if key in self.windows: return self.windows[key]
        a,b = self.observations[before_id],self.observations[after_id]
        valid = (a.tray_id == b.tray_id and a.time_s < b.time_s and
                 a.fully_visible and b.fully_visible and a.aligned and b.aligned and
                 a.count is not None and b.count is not None and b.count <= a.count)
        # Overlapping inventory intervals cannot supply the same removed blocks twice.
        for old in self.windows.values():
            if old['budget'] is not None and a.tray_id == old['tray_id'] and max(a.time_s, old['start']) < min(b.time_s, old['end']):
                raise ValueError('Overlapping inventory budget; reuse the same window')
        result = dict(tray_id=a.tray_id,start=a.time_s,end=b.time_s,
            budget=a.count-b.count if valid else None, claimed=0,
            reason='observed net removal; not placement' if valid else 'incomplete or unmatched inventory evidence')
        self.windows[key]=result
        return result

    def claim(self, load_id, before_id, after_id, quantity, pickup_s):
        payload=(before_id,after_id,quantity,pickup_s)
        if load_id in self.claims:
            if self.claims[load_id]['payload'] != payload: raise ValueError('Conflicting load claim')
            return self.claims[load_id]['supported']
        if not load_id or not math.isfinite(pickup_s): raise ValueError('Load identity and time required')
        w=self.window(before_id,after_id)
        ok=(type(quantity) is int and quantity>0 and w['budget'] is not None and
            w['start'] <= pickup_s <= w['end'] and w['claimed']+quantity <= w['budget'])
        if ok:w['claimed']+=quantity
        self.claims[load_id]=dict(payload=payload,supported=ok,quantity=quantity,released=0,closed=False)
        return ok

    def release(self, event_id, load_id, quantity, time_s, destination, tank_id, release_observed):
        payload=(load_id,quantity,time_s,destination,tank_id,release_observed)
        if event_id in self.releases:
            if self.releases[event_id]['payload'] != payload: raise ValueError('Conflicting release')
            return 0
        if not event_id or not math.isfinite(time_s): raise ValueError('Release identity and time required')
        claim=self.claims.get(load_id)
        valid=(claim is not None and claim['supported'] and not claim['closed'] and release_observed is True and
            destination=='filling_tank' and bool(tank_id) and type(quantity) is int and quantity>0 and
            time_s >= claim['payload'][3] and claim['released']+quantity <= claim['quantity'])
        accepted=quantity if valid else 0
        if valid:claim['released']+=quantity
        if claim is not None and release_observed is True and destination in {'same_tray','conveyor_return','crumb_tank'}:
            # This physical load has left the transfer. A fresh pickup needs fresh evidence.
            claim['closed']=True
        self.releases[event_id]=dict(payload=payload,accepted=accepted)
        return accepted

    def report(self):
        counts={}
        for r in self.releases.values():
            if r['accepted']:
                tank=r['payload'][4]; counts[tank]=counts.get(tank,0)+r['accepted']
        return dict(evidence_supported_additions=counts, inference_implemented=False,
            note='Only supplied observations are checked. Passing logic tests does not establish vision accuracy.')
