"""Base class and result dataclass for page replacement algorithms."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
import time

PAGE_SIZE_BYTES = 4096  # 4 KB per page (standard)


@dataclass
class StepRecord:
    """State snapshot after processing one page reference."""
    reference: int
    frames: List[int]
    is_fault: bool
    victim: Optional[int]      # page evicted (None if no eviction)
    loaded: Optional[int]      # page loaded (None if hit)
    reference_bits: List[int]  # for Clock algorithm; empty otherwise


@dataclass
class SimulationResult:
    """All metrics and history for a single algorithm run."""
    algorithm_name: str
    reference_string: List[int]
    num_frames: int
    steps: List[StepRecord] = field(default_factory=list)
    page_faults: int = 0
    page_hits: int = 0
    execution_time_ns: float = 0.0   # nanoseconds (perf_counter_ns)
    # Simulated OS metrics
    system_calls: int = 0            # = page_faults (each fault → handle_page_fault syscall)
    interrupts: int = 0              # = page_faults (hardware page-fault interrupt per fault)

    # ── Derived properties ────────────────────────────────────────────────────
    @property
    def total_references(self) -> int:
        return len(self.reference_string)

    @property
    def hit_ratio(self) -> float:
        if self.total_references == 0:
            return 0.0
        return self.page_hits / self.total_references

    @property
    def fault_ratio(self) -> float:
        if self.total_references == 0:
            return 0.0
        return self.page_faults / self.total_references

    @property
    def execution_time_us(self) -> float:
        return self.execution_time_ns / 1_000

    @property
    def execution_time_ms(self) -> float:
        return self.execution_time_ns / 1_000_000

    @property
    def memory_used_bytes(self) -> int:
        return self.num_frames * PAGE_SIZE_BYTES

    @property
    def memory_used_kb(self) -> float:
        return self.memory_used_bytes / 1024


class PageReplacementAlgorithm:
    """Abstract base for all page-replacement algorithms."""

    name: str = "Base"

    def __init__(self, num_frames: int):
        self.num_frames = num_frames
        self._frames: List[int] = []

    def reset(self) -> None:
        self._frames = []

    def step(self, page: int, future: Optional[List[int]] = None) -> StepRecord:
        raise NotImplementedError

    def run(self, reference_string: List[int]) -> SimulationResult:
        self.reset()
        result = SimulationResult(
            algorithm_name=self.name,
            reference_string=list(reference_string),
            num_frames=self.num_frames,
        )
        start = time.perf_counter_ns()
        for i, page in enumerate(reference_string):
            future = reference_string[i + 1:]
            record = self.step(page, future)
            result.steps.append(record)
            if record.is_fault:
                result.page_faults += 1
                result.system_calls += 1
                result.interrupts += 1
            else:
                result.page_hits += 1
        result.execution_time_ns = time.perf_counter_ns() - start
        return result
