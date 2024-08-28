from dataclasses import dataclass
from typing import Callable, Sequence


@dataclass
class SystemDynamics:
    """
    Represents the system dynamics function that maps a state, action, and disturbance to a new state.

    Attributes:
        f (Callable[[Tuple[float], Tuple[float], Tuple[float]], Tuple[float]]):
            A function representing the system dynamics. The function takes three tuples
            (state, action, disturbance) and returns a tuple representing the new state.
    """
    f: Callable[[State, Tuple[float], Tuple[float]], Tuple[float]]
