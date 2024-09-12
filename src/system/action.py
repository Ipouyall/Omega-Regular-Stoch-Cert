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
class SystemControlAction:
    action_values: Sequence[Number]
    dimension: int

    __slots__ = ["action_values", "dimension"]

    def __post_init__(self):
        if self.dimension is None:
            logger.warning("The dimension of the action space has not been set. Attempting to infer the dimension from the number of action values.")
            self.dimension = len(self.action_values)
        if len(self.action_values) != self.dimension:
            logger.warning(f"The number of action values does not match the dimension of the action space \
            ({len(self.action_values)} != {self.dimension}). Correcting the dimension based on the number of action values.")

        if self.dimension == 0:
            raise ValueError("The dimension of the action space must be greater than 0.")

    def __call__(self, *args, **kwargs):
        return {
            f"P{i}": p for i, p in enumerate(self.action_values, start=1)
        }

    def __str__(self):
        return f"Action π{self.dimension}: {self.action_values}"


@dataclass
class SystemControlPolicy:
    action_space: Space
    state_dimension: int
    maximal_degree: int
    transitions: Union[None, Sequence[Equation]] = None
    verification_mode: bool = field(init=False, default=False)
    generated_constants: set[str] = field(init=False, default_factory=set)
    constant_founded: bool = field(init=False, default=False)

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
            self.transitions = [
                Equation.extract_equation_from_string(str(equation))
                for equation in self.transitions
            ]
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

    def _found_constants(self) -> None:
        """Constants are in the form of `P{i}_{j}` where `i` is the action index and `j` is the monomial index."""
        self.constant_founded = True
        for equation in self.transitions:
            for monomial in equation.monomials:
                for variable in monomial.variable_generators:
                    if variable.startswith("P") and variable not in self.generated_constants:
                        self.generated_constants.add(variable)


    def get_generated_constants(self) -> set[str]:
        if not self.constant_founded:
            self._found_constants()
        return self.generated_constants

    def __call__(self, state: SystemState) -> SystemControlAction:
        # if not isinstance(state, SystemState):
        #     raise TypeError(f"Expected state to be of type SystemState, got {type(state)}")
        if state.dimension != self.state_dimension:
            raise ValueError(f"State dimension does not match the expected state dimension ({state.dimension} != {self.state_dimension}).")
        if not self.transitions:
            raise ValueError("Control policy is not provided.")

        args = state()
        return SystemControlAction(
            dimension=self.action_space.dimension,
            action_values=[
                equation(**args)
                for equation in self.transitions
            ]
        )



