from dataclasses import dataclass
from typing import List, Dict

from .polynomial.equation import Equation


@dataclass
class SystemDynamics:
    """
    Represents the system dynamics function that maps a state, action, and disturbance to a new state.
    """
    state_dimension: int
    action_dimension: int
    disturbance_dimension: int
    system_transformations: List[Equation]

    def __post_init__(self):
        if len(self.system_transformations) == 0:
            raise ValueError("At least one system transformer must be provided.")

        for transformer in self.system_transformations:
            if not isinstance(transformer, Equation):
                raise TypeError(f"Expected system transformer to be of type Equation, got {type(transformer)}.")

        if len(self.system_transformations) != self.state_dimension:
            raise ValueError(f"The number of system transformers must match the state dimension. ({len(self.system_transformations)} != {self.state_dimension})")

    def __call__(self, args: Dict) -> Dict[str, str]:
        """
        Feed in the noise values of you want to do the evaluation, otherwise feed the expectations.
        """
        return {
            f"S{i}": transformer(**args)
            for i, transformer in enumerate(self.system_transformations, start=1)
        }

