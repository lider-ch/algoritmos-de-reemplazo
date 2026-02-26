"""Clock (Second Chance) page replacement algorithm."""
from typing import List, Optional
from .base import PageReplacementAlgorithm, StepRecord


class ClockAlgorithm(PageReplacementAlgorithm):
    name = "Clock (Segunda Oportunidad)"

    def reset(self) -> None:
        self._frames = [-1] * self.num_frames   # -1 = empty slot
        self._ref_bits = [0] * self.num_frames  # reference bits
        self._pointer = 0                        # clock hand

    def step(self, page: int, future: Optional[List[int]] = None) -> StepRecord:
        victim = None
        loaded = None

        # Check if page already in a frame
        if page in self._frames:
            idx = self._frames.index(page)
            self._ref_bits[idx] = 1   # set reference bit (recently used)
            is_fault = False
        else:
            is_fault = True
            loaded = page
            # Advance clock hand until we find a frame with ref_bit = 0
            while True:
                if self._frames[self._pointer] == -1:
                    # empty slot – load immediately
                    self._frames[self._pointer] = page
                    self._ref_bits[self._pointer] = 1
                    self._pointer = (self._pointer + 1) % self.num_frames
                    break
                elif self._ref_bits[self._pointer] == 0:
                    # evict this page
                    victim = self._frames[self._pointer]
                    self._frames[self._pointer] = page
                    self._ref_bits[self._pointer] = 1
                    self._pointer = (self._pointer + 1) % self.num_frames
                    break
                else:
                    # give second chance
                    self._ref_bits[self._pointer] = 0
                    self._pointer = (self._pointer + 1) % self.num_frames

        visible_frames = [f for f in self._frames if f != -1]
        return StepRecord(
            reference=page,
            frames=visible_frames,
            is_fault=is_fault,
            victim=victim,
            loaded=loaded,
            reference_bits=list(self._ref_bits),
        )
