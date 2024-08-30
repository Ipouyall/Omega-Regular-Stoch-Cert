from copy import deepcopy
from dataclasses import dataclass
from numbers import Number
from typing import Sequence, Union
from itertools import product

from .space import Space
from .equation import Equation, Monomial
from .state import SystemState


@dataclass
class SystemAction:
    action: Sequence[Number]


@dataclass
class SystemControlPolicy:
    action_space: Space
    state_dimension: int
    maximal_degree: int
    transitions: Union[None, Sequence[Equation]] = None

    # TODO: add "action validation" and "next action" methods

    def __post_init__(self):
        if self.transitions is None or not self.transitions:
            self._initialize_control_policy()

    def update_control_policy(self, new_policy: Sequence[Equation]) -> None:
        self.transitions = deepcopy(new_policy)

    def _initialize_control_policy(self) -> None:
        _transitions = []
        variable_generators = [f"S{i}" for i in range(1, self.state_dimension + 1)]
        power_combinations = product(range(self.maximal_degree + 1), repeat=self.state_dimension)
        power_combinations = [powers for powers in power_combinations if sum(powers) <= self.maximal_degree]

        for i in range(1, self.action_space.dimension+1):
            _monomials = [
                Monomial(
                    symbolic_coefficient=f"P{i}_{i2}",
                    variable_generators=variable_generators,
                    power=powers
                ) for i2, powers in enumerate(power_combinations, start=1)
            ]
            _equation = Equation(monomials=_monomials)
            _transitions.append(_equation)
        self.transitions = _transitions

    def __call__(self, state: SystemState) -> SystemAction: pass # TODO: implement this method after designing communication API


