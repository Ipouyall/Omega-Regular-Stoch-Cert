from copy import deepcopy
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

    def __call__(self, state: list[float], actions: list, noises: list[float], evaluate: bool = False) -> list:
        """
        Feed in the noise values of you want to do the evaluation, otherwise feed the expectations.
        """

        ss = {f"S{i}": s for i, s in enumerate(state, start=1)}
        aa = {f"A{i}": a for i, a in enumerate(actions, start=1)}
        dd = {f"D{i}": d for i, d in enumerate(noises, start=1)}
        return [
            transform(**ss, **aa, **dd, evaluate=evaluate)
            for transform in self.system_transformers
        ]

