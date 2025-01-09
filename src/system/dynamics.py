from dataclasses import dataclass
from typing import List, Dict

from .polynomial.equation import Equation
from .polynomial.inequality import Inequality


@dataclass
class ConditionalDynamics:
    condition: List[Inequality]
    dynamics: List[Equation]

    def condition_to_string(self):
        return " and ".join([c.to_detailed_string() for c in self.condition])

    def __len__(self):
        return len(self.dynamics)

    def __call__(self, args) -> Dict[str, str]:
        return {
            f"S{i}": transformer(**args)
            for i, transformer in enumerate(self.dynamics, start=1)
        }



@dataclass
class SystemDynamics:
    """
    Represents the system dynamics function that maps a state, action, and disturbance to a new state.
    """
    state_dimension: int
    action_dimension: int
    disturbance_dimension: int
    system_transformations: List[ConditionalDynamics]

    def __post_init__(self):
        if len(self.system_transformations) == 0:
            raise ValueError("At least one system transformer must be provided.")

        for transformer in self.system_transformations:
            if not isinstance(transformer, ConditionalDynamics):
                raise TypeError(f"Expected system transformer to be of type ConditionalEquation, got {type(transformer)}.")

        for dynamics in self.system_transformations:
            if len(dynamics) != self.state_dimension:
                raise ValueError(f"The number of system transformers must match the state dimension. ({len(self.system_transformations)} != {self.state_dimension})")

    def __call__(self, args: Dict):
        """
        Feed in the noise values of you want to do the evaluation, otherwise feed the expectations.
        """
        return NotImplemented

