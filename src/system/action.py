from copy import deepcopy
from dataclasses import dataclass, field
from numbers import Number
from typing import Sequence, Union
from itertools import product

from . import logger
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
    verification_mode: bool = field(init=False, default=False)

    # TODO: add "action validation" and "next action" methods

    def __post_init__(self):
        if not isinstance(self.action_space, Space):
            raise TypeError(f"Expected action_space to be of type Space, got {type(self.action_space)}")
        if self.transitions is not None and len(self.transitions) != self.action_space.dimension:
            logger.error(f"No valid control policy provided. Ignoring the provided policy.")
            logger.info(f"Number of control policy equations must match the action space dimension. Expected {self.action_space.dimension} equations, got {len(self.transitions)}.")
            self.transitions = None
        if self.transitions is None or not self.transitions:
            self.verification_mode = False
            logger.info("No control policy provided. Initializing a default control policy.")
            self._initialize_control_policy()
        else:
            self.verification_mode = True
            logger.info("Control policy provided. Verification mode is enabled.")

    def update_control_policy(self, new_policy: Sequence[Equation]) -> None:
        self.transitions = deepcopy(new_policy)

    def _initialize_control_policy(self) -> None:
        logger.info(f"Initializing a control policy template with a maximal degree of {self.maximal_degree}, for space dimension {self.state_dimension} and action space dimension {self.action_space.dimension}.")
        _transitions = []
        variable_generators = [f"S{i}" for i in range(1, self.state_dimension + 1)]
        power_combinations = product(range(self.maximal_degree + 1), repeat=self.state_dimension)
        power_combinations = [powers for powers in power_combinations if sum(powers) <= self.maximal_degree]

        for i in range(1, self.action_space.dimension+1):
            _monomials = [
                Monomial(
                    coefficient=1,
                    variable_generators=variable_generators + [f"P{i}_{i2}"],
                    power=powers + (1,)
                ) for i2, powers in enumerate(power_combinations, start=1)
            ]
            _equation = Equation(monomials=_monomials)
            _transitions.append(_equation)
        self.transitions = _transitions

    def __call__(self, state: SystemState) -> SystemAction: pass # TODO: implement this method after designing communication API


