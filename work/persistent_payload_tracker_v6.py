"""Persistent load association experiment; never a verified production counter.

Consumes unchanged image-detector outputs. Only association changes from v5.
End-of-track disappearance remains a *candidate* release, not proof of release.
No reference count, tray capacity, worker identity, or September data is input.
"""
from copy import deepcopy
import math
import numpy as np
from evaluate_payload_counter_v5 import Counter, CONFIG as V5_CONFIG

CONFIG = dict(deepcopy(V5_CONFIG), maximum_gap_s=1.2,
    maximum_match_distance_px=100, association='global minimum-cost assignment with unmatched nodes',
    maximum_speed_px_s=300, base_gate_px=22, velocity_horizon_s=.25,
    velocity_decay_s=.35, quantity_disagreement_cost=12,
    source_return_break_px=70, ambiguous_cost_margin_px=5,
    experiment='v6 association-only; fixed v5 detector and candidate-release geometry',
    limitations='A prolonged association can merge unrelated loads. Gaps, splits, and quantity changes are recorded. Disappearance still does not verify release.')


def minimum_assignment(cost):
    """Rectangular Hungarian assignment, rows <= columns, finite costs.

    Callers append one unmatched node per track. No scipy dependency.
    """
    a = np.asarray(cost, dtype=float)
    if a.ndim != 2 or not np.isfinite(a).all():
        raise ValueError('Finite 2D costs required')
    n, m = a.shape
    if n > m:
        raise ValueError('Need at least as many columns as rows')
    u = np.zeros(n + 1); v = np.zeros(m + 1)
    p = np.zeros(m + 1, dtype=int); way = np.zeros(m + 1, dtype=int)
    for i in range(1, n + 1):
        p[0] = i; j0 = 0
        minv = np.full(m + 1, np.inf); used = np.zeros(m + 1, dtype=bool)
        while True:
            used[j0] = True; i0 = p[j0]; delta = np.inf; j1 = 0
            for j in range(1, m + 1):
                if used[j]: continue
                cur = a[i0 - 1, j - 1] - u[i0] - v[j]
                if cur < minv[j]: minv[j] = cur; way[j] = j0
                if minv[j] < delta: delta = minv[j]; j1 = j
            for j in range(m + 1):
                if used[j]: u[p[j]] += delta; v[j] -= delta
                else: minv[j] -= delta
            j0 = j1
            if p[j0] == 0: break
        while True:
            j1 = way[j0]; p[j0] = p[j1]; j0 = j1
            if j0 == 0: break
    return [(int(p[j] - 1), j - 1) for j in range(1, m + 1) if p[j]]


def projection(point):
    return float(point[0] + .8 * point[1])


class PersistentCounter(Counter):
    def __init__(self, config=None):
        super().__init__(deepcopy(CONFIG if config is None else config))
        self.last_time = None

    def close(self, track, now, cutoff=False):
        super().close(track, now, cutoff)
        event = (self.events if self.events and self.events[-1]['track_id'] == track['id']
                 else self.rejected)[-1]
        gaps = np.diff([o['time_s'] for o in track['history']])
        event.update(maximum_observation_gap_s=float(max(gaps, default=0)),
            bridged_gaps=sum(float(g) > V5_CONFIG['maximum_gap_s'] for g in gaps),
            ambiguous_associations=track.get('ambiguous_associations', 0),
            release_verified=False, source_inventory_verified=False,
            interpretation='Experimental trajectory candidate, not confirmed addition')

    def step(self, t, detections):
        if not math.isfinite(t) or (self.last_time is not None and t <= self.last_time):
            raise ValueError('Strictly increasing finite source timestamps required')
        self.last_time = float(t)
        for ident, track in list(self.active.items()):
            if t - track['history'][-1]['time_s'] > self.c['maximum_gap_s']:
                self.close(track, t); del self.active[ident]
        ds = []
        for d in detections:
            box = np.asarray(d['bbox'], dtype=float)
            if box.shape != (4,) or not np.isfinite(box).all() or np.any(box[2:] <= box[:2]):
                raise ValueError('Positive finite bounding box required')
            ds.append(dict(bbox=box.tolist(), confidence=float(d['confidence']),
                quantity=int(d['quantity']), center=((box[:2]+box[2:])/2).tolist(), time_s=float(t)))
        ids = list(self.active); n = len(ids); m = len(ds)
        unmatched_cost = 125.; cost = np.full((n, m+n), 1e6)
        for i, ident in enumerate(ids):
            h = self.active[ident]['history']; last = h[-1]
            gap = t-last['time_s']; point = np.array(last['center'])
            speed = np.zeros(2)
            if len(h) >= 2:
                previous = h[max(0, len(h)-4)]
                speed = (point-np.array(previous['center'])) / max(last['time_s']-previous['time_s'], .02)
                speed = np.clip(speed, -self.c['maximum_speed_px_s'], self.c['maximum_speed_px_s'])
            predicted = point + speed * min(gap,self.c['velocity_horizon_s']) * math.exp(-gap/self.c['velocity_decay_s'])
            gate = min(self.c['maximum_match_distance_px'], self.c['base_gate_px'] + self.c['maximum_speed_px_s']*gap)
            for j, d in enumerate(ds):
                q = np.asarray(d['center']); distance = float(np.linalg.norm(predicted-q))
                # A return from the tank to a new pickup must start a fresh load.
                if (projection(point) < self.c['destination_projection_max']
                        and projection(q)-projection(point) > self.c['source_return_break_px']
                        and projection(q) >= self.c['source_projection_min']): continue
                if distance > gate: continue
                penalty = self.c['quantity_disagreement_cost'] if d['quantity'] and last['quantity'] and d['quantity'] != last['quantity'] else 0
                cost[i,j] = distance + penalty
            cost[i,m+i] = unmatched_cost
        used = set(); output = []
        for i,j in minimum_assignment(cost) if n else []:
            if j >= m or cost[i,j] >= unmatched_cost: continue
            ident = ids[i]; track = self.active[ident]
            alternatives = [cost[k,j] for k in range(n) if k != i and cost[k,j] < unmatched_cost]
            if alternatives and min(alternatives)-cost[i,j] < self.c['ambiguous_cost_margin_px']:
                track['ambiguous_associations'] += 1
            track['history'].append(ds[j]); used.add(j)
            output.append(dict(ds[j], track_id=ident))
        for j,d in enumerate(ds):
            if j in used: continue
            ident = self.next_id; self.next_id += 1; x,y=d['center']
            self.active[ident] = dict(id=ident,side='L' if y>.7*x+80 else 'R', history=[d], ambiguous_associations=0)
            output.append(dict(d,track_id=ident))
        return output
