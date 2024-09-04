from dataclasses import dataclass
from typing import List, Union

from .action import SystemControlAction
from .equation import Equation
from .state import SystemState


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

    def __call__(self, state: SystemState, action: SystemControlAction, noise: Union[None, list[float]], evaluate: bool = False) -> SystemState:
        """
        Feed in the noise values of you want to do the evaluation, otherwise feed the expectations.
        """

        args = {}
        if state is not None:
            args.update(state())
        if action is not None:
            args.update(action())
        if noise is not None:
            args.update({f"D{i}": d for i, d in enumerate(noise, start=1)})

        return SystemState(
            dimension=self.state_dimension,
            state_values=[
                transformer(**args, evaluate=evaluate)
                for transformer in self.system_transformers
            ]
        )

