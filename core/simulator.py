"""Simulator: orchestrates algorithm execution and returns results."""
from __future__ import annotations
import random
from typing import List
from algorithms import ALGORITHMS
from algorithms.base import SimulationResult


def run_single(algo_key: str, reference_string: List[int], num_frames: int) -> SimulationResult:
    """Run one algorithm and return its SimulationResult."""
    cls = ALGORITHMS[algo_key]
    algo = cls(num_frames)
    return algo.run(reference_string)


def run_all(reference_string: List[int], num_frames: int) -> List[SimulationResult]:
    """Run all registered algorithms with the same inputs and return results list."""
    results = []
    for key in ALGORITHMS:
        results.append(run_single(key, reference_string, num_frames))
    return results


def generate_reference_string(num_pages: int, length: int, seed: int | None = None) -> List[int]:
    """Generate a random page reference string."""
    if seed is not None:
        random.seed(seed)
    return [random.randint(0, num_pages - 1) for _ in range(length)]
