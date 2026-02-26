"""LFU – Least Frequently Used page replacement algorithm."""
from collections import defaultdict, OrderedDict
from typing import List, Optional
from .base import PageReplacementAlgorithm, StepRecord


class LFUAlgorithm(PageReplacementAlgorithm):
    name = "LFU (Least Frequently Used)"

    def reset(self) -> None:
        super().reset()
        self._freq: dict = defaultdict(int)  # page → use count
        self._order: OrderedDict = OrderedDict()  # FIFO tiebreaker

    def step(self, page: int, future: Optional[List[int]] = None) -> StepRecord:
        victim = None
        loaded = None
        is_fault = page not in self._frames

        if is_fault:
            loaded = page
            if len(self._frames) < self.num_frames:
                self._frames.append(page)
                self._order[page] = True
            else:
                # find page with lowest frequency; FIFO tiebreaker via _order
                min_freq = min(self._freq[p] for p in self._frames)
                # preserve insertion order among ties
                for p in list(self._order.keys()):
                    if p in self._frames and self._freq[p] == min_freq:
                        victim = p
                        break
                # reset evicted page counters
                self._freq[victim] = 0
                del self._order[victim]
                self._frames[self._frames.index(victim)] = page
                self._order[page] = True
        else:
            # Update order on hit (move to end to indicate recent use)
            if page in self._order:
                self._order.move_to_end(page)

        self._freq[page] += 1

        return StepRecord(
            reference=page,
            frames=list(self._frames),
            is_fault=is_fault,
            victim=victim,
            loaded=loaded,
            reference_bits=[],
        )
