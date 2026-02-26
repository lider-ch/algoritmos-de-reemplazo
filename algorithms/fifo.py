"""FIFO – First In, First Out page replacement algorithm."""
from collections import deque
from typing import List, Optional
from .base import PageReplacementAlgorithm, StepRecord


class FIFOAlgorithm(PageReplacementAlgorithm):
    name = "FIFO (First In, First Out)"

    def reset(self) -> None:
        super().reset()
        self._queue: deque = deque()   # tracks arrival order

    def step(self, page: int, future: Optional[List[int]] = None) -> StepRecord:
        victim = None
        loaded = None
        is_fault = page not in self._frames

        if is_fault:
            loaded = page
            if len(self._frames) < self.num_frames:
                self._frames.append(page)
                self._queue.append(page)
            else:
                # evict the oldest arrival
                victim = self._queue.popleft()
                self._frames[self._frames.index(victim)] = page
                self._queue.append(page)

        return StepRecord(
            reference=page,
            frames=list(self._frames),
            is_fault=is_fault,
            victim=victim,
            loaded=loaded,
            reference_bits=[],
        )
