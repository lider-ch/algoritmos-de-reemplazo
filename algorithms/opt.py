"""OPT – Optimal (Bélády) page replacement algorithm."""
from typing import List, Optional
from .base import PageReplacementAlgorithm, StepRecord


class OPTAlgorithm(PageReplacementAlgorithm):
    name = "OPT – Óptimo (Bélády)"

    def _next_use(self, page: int, future: List[int]) -> int:
        """Return index of next use in future, or infinity if never used again."""
        for i, p in enumerate(future):
            if p == page:
                return i
        return float("inf")

    def step(self, page: int, future: Optional[List[int]] = None) -> StepRecord:
        future = future or []
        victim = None
        loaded = None
        is_fault = page not in self._frames

        if is_fault:
            loaded = page
            if len(self._frames) < self.num_frames:
                self._frames.append(page)
            else:
                # evict page that won't be needed for longest time
                victim_page = max(self._frames, key=lambda p: self._next_use(p, future))
                victim = victim_page
                self._frames[self._frames.index(victim_page)] = page

        return StepRecord(
            reference=page,
            frames=list(self._frames),
            is_fault=is_fault,
            victim=victim,
            loaded=loaded,
            reference_bits=[],
        )
