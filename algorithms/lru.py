"""LRU – Least Recently Used page replacement algorithm."""
from typing import List, Optional
from .base import PageReplacementAlgorithm, StepRecord


class LRUAlgorithm(PageReplacementAlgorithm):
    name = "LRU (Least Recently Used)"

    def reset(self) -> None:
        super().reset()
        self._last_use: dict = {}   # page -> last access index
        self._tick: int = 0

    def step(self, page: int, future: Optional[List[int]] = None) -> StepRecord:
        victim = None
        loaded = None
        is_fault = page not in self._frames

        if is_fault:
            loaded = page
            if len(self._frames) < self.num_frames:
                self._frames.append(page)
            else:
                # evict page whose last use is oldest
                lru_page = min(self._frames, key=lambda p: self._last_use.get(p, -1))
                victim = lru_page
                self._frames[self._frames.index(lru_page)] = page

        self._last_use[page] = self._tick
        self._tick += 1

        return StepRecord(
            reference=page,
            frames=list(self._frames),
            is_fault=is_fault,
            victim=victim,
            loaded=loaded,
            reference_bits=[],
        )
