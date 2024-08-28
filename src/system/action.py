from copy import deepcopy
from dataclasses import dataclass
from numbers import Number
from typing import Sequence

from src.system import Space
from src.system.equation import Equation
from src.system.state import SystemState


@dataclass
class SystemAction:
    action: Sequence[Number]


@dataclass
class SystemControlPolicy:
    action_space: Space
    dimension: int
    transitions: Sequence[Equation]

    # TODO: add "action validation" and "next action" methods

    def update_control_policy(self, new_policy: Sequence[Equation]) -> None:
        self.transitions = deepcopy(new_policy)

    def _initialize_control_policy(self) -> None:
        _transitions = []
        for dim_num, _ in enumerate(range(self.dimension)): pass # TODO: add equation for each dimension


    def __call__(self, state: SystemState) -> SystemAction: pass # TODO: implement this method after designing communication API


