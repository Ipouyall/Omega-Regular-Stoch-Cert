from dataclasses import dataclass
from typing import List

from .equation import Equation


@dataclass
class SystemDynamics:
    """
    Represents the system dynamics function that maps a state, action, and disturbance to a new state.

    Attributes:
        f (Callable[[Tuple[float], Tuple[float], Tuple[float]], Tuple[float]]):
            A function representing the system dynamics. The function takes three tuples
            (state, action, disturbance) and returns a tuple representing the new state.
    """
    state_dimension: int
    action_dimension: int
    disturbance_dimension: int
    system_transformers: List[Equation]

    def __post_init__(self):
        if len(self.system_transformers) == 0:
            raise ValueError("At least one system transformer must be provided.")

        if len(self.system_transformers) != self.state_dimension:
            raise ValueError(f"The number of system transformers must match the state dimension. ({len(self.system_transformers)} != {self.state_dimension})")
