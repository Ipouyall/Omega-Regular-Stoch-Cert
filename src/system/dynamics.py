from dataclasses import dataclass
from typing import List

from .equation import Equation


@dataclass
class SystemDynamics:
    """
    Represents the system dynamics function that maps a state, action, and disturbance to a new state.
    """
    state_dimension: int
    action_dimension: int
    disturbance_dimension: int
    system_transformers: List[Equation]

    def __post_init__(self):
        if len(self.system_transformers) == 0:
            raise ValueError("At least one system transformer must be provided.")

        for transformer in self.system_transformers:
            if not isinstance(transformer, Equation):
                raise TypeError(f"Expected system transformer to be of type Equation, got {type(transformer)}.")

        if len(self.system_transformers) != self.state_dimension:
            raise ValueError(f"The number of system transformers must match the state dimension. ({len(self.system_transformers)} != {self.state_dimension})")

    def __call__(self, state: list[float], action: list, noise: list[float], evaluate: bool = False) -> list:
        """
        Feed in the noise values of you want to do the evaluation, otherwise feed the expectations.
        """

        ss = {f"S{i}": s for i, s in enumerate(state, start=1)}
        aa = {f"A{i}": a for i, a in enumerate(action, start=1)}
        dd = {f"D{i}": d for i, d in enumerate(noise, start=1)}
        return [
            transform(**ss, **aa, **dd, evaluate=evaluate)
            for transform in self.system_transformers
        ]

