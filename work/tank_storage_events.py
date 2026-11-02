"""Room 11 event rule. Upstream vision must supply evidence, not guesses.

An episode follows one tank from filling through exit. It is NOT a tracker ID:
upstream association must preserve it across occlusions and start a new episode
after a return/refill. This module does not recognize cheese or read clocks.
"""
from dataclasses import dataclass, field
from datetime import datetime


def timestamp(value: str) -> datetime:
    result = datetime.fromisoformat(value)
    if result.utcoffset() is None:
        raise ValueError('Camera timestamp must include its verified UTC offset')
    return result


@dataclass
class StorageCounter:
    filled: dict = field(default_factory=dict)
    emitted: dict = field(default_factory=dict)
    uncertain: set = field(default_factory=set)

    def observe_filling(self, episode: str, at: str, evidence: str, *,
                        cheese_placed: bool, designated_station_workers: bool):
        """No amount/fullness test. Liners, presence, or dwell time do not qualify."""
        timestamp(at)
        if not episode or not evidence:
            raise ValueError('Episode and evidence reference are required')
        if cheese_placed and designated_station_workers:
            if episode in self.emitted:
                raise ValueError('A new filling cycle requires a new episode')
            self.filled.setdefault(episode, {'at': at, 'evidence': evidence})

    def lose_continuity(self, episode: str):
        self.uncertain.add(episode)

    def observe_crossing(self, episode: str, at: str, evidence: str, *,
                         room: int, direction: str):
        exit_at = timestamp(at)
        if not evidence:
            raise ValueError('Exit evidence is required')
        if room != 11 or direction != 'outbound':
            return None
        if episode in self.emitted or episode in self.uncertain:
            return None
        filling = self.filled.get(episode)
        if not filling or exit_at < timestamp(filling['at']):
            return None
        event = {'event': 'tank_storage', 'exited_at': at,
                 'episode': episode, 'filling_evidence': filling['evidence'],
                 'exit_evidence': evidence}
        self.emitted[episode] = event
        return event

    def user_records(self):
        """Only the requested event and date/time; provenance stays internal."""
        return [{'event': 'tank_storage', 'exited_at': e['exited_at']}
                for e in sorted(self.emitted.values(), key=lambda e: timestamp(e['exited_at']))]
