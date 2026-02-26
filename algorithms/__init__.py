from .fifo import FIFOAlgorithm
from .lru import LRUAlgorithm
from .opt import OPTAlgorithm
from .clock import ClockAlgorithm
from .lfu import LFUAlgorithm

ALGORITHMS = {
    "FIFO": FIFOAlgorithm,
    "LRU":  LRUAlgorithm,
    "OPT":  OPTAlgorithm,
    "Clock": ClockAlgorithm,
    "LFU":  LFUAlgorithm,
}
