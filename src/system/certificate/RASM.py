from dataclasses import dataclass, field
from itertools import product
from textwrap import fill

from .. import logger
from .constraints import NonNegativityConstraint, InitialLessThanOneConstraint, SafetyConstraint, \
    DecreaseExpectationConstraint, ConstraintInequality
from ..equation import Equation
from ..polynomial import Monomial
from ..toolIO import ToolInput


@dataclass
class ReachAvoidSuperMartingaleCertificate:
    maximal_degree: int
    state_dimension: int
    function: Equation = field(init=False, default=None)
    constraints: list[ConstraintInequality] = field(init=False, default=None)

    def __post_init__(self):
        self._initialize_rasm_function()

    def _initialize_rasm_function(self):
        logger.info(
            f"Initializing the V(x) function for the RASM certificate with a maximal degree of {self.maximal_degree} for a state space of dimension {self.state_dimension}."
        )
        _state_variable_gens = [f"S{i}" for i in range(1, self.state_dimension + 1)]
        power_combinations = [
            powers
            for powers in product(range(self.maximal_degree + 1), repeat=self.state_dimension)
            if sum(powers) <= self.maximal_degree
        ]
        _monomials = [
            Monomial(
                coefficient=1,
                variable_generators=_state_variable_gens + [f"V{i}"],
                power=powers + (1,)
            ) for i, powers in enumerate(power_combinations, start=1)
        ]
        self.function = Equation(monomials=_monomials)

    def define_constraints(self, data: ToolInput):
        non_negativity = NonNegativityConstraint(
            v_function=self.function,
            state_space=data.state_space,
        )
        initial_bounded = InitialLessThanOneConstraint(
            v_function=self.function,
            initial_state_space=data.initial_states,
        )
        safety = SafetyConstraint(
            v_function=self.function,
            unsafe_state_space=data.unsafe_states,
            probability_threshold=data.probability_threshold,
        )
        decrease_expectation = DecreaseExpectationConstraint(
            v_function=self.function,
            state_space=data.state_space,
            target_state_space=data.target_states,
            action_policy=data.action_policy,
            system_dynamics=data.dynamics,
            system_disturbance=data.disturbance,
            maximal_equation_degree=self.maximal_degree,
            epsilon=data.synthesis_config.epsilon,
        )

        self.constraints = [
            non_negativity.extract(),
            initial_bounded.extract(),
            safety.extract(),
            # decrease_expectation.extract(),
        ]

    def __str__(self) -> str:
        constraints_str = "\n+\t".join(
            fill(str(constraint), width=100, subsequent_indent=" \t", initial_indent="")
            for constraint in self.constraints
        )
        printable_v_function = fill(str(self.function), width=100, subsequent_indent=" \t", initial_indent="")
        return f"RASM Certificate: \n+\tV(x) = {printable_v_function} \n- Constraints:\n+\t{constraints_str}"

