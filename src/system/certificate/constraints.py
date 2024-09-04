from abc import ABC, abstractmethod
from dataclasses import dataclass
import re

from ..action import SystemControlPolicy
from ..dynamics import SystemDynamics
from ..equation import Equation, ConditionalEquation, EquationConditionType
from ..noise import SystemStochasticNoise
from ..polynomial import Monomial
from ..space import Space
from ..state import SystemState


class Constraint(ABC):

    # def __post_init__(self):
    #     """Check the type of the attributes and log or raise an error if the types don't match."""
    #     for attr_name, attr_type in get_type_hints(self.__class__).items():
    #         attr_value = getattr(self, attr_name)
    #         if not isinstance(attr_value, attr_type):
    #             raise TypeError(
    #                 f"Attribute '{attr_name}' is expected to be of type {attr_type}, but got {type(attr_value)} instead."
    #             )

    @abstractmethod
    def extract(self) -> ConditionalEquation:
        pass


def _replace_keys_with_values(s, dictionary):
    pattern = re.compile("|".join(re.escape(key) for key in dictionary.keys()))
    result = pattern.sub(lambda match: dictionary[match.group(0)], s)
    return result


@dataclass
class NonNegativityConstraint(Constraint):
    """
    forall x ∈ X → V(x) ≥ 0
    """
    v_function: Equation
    state_space: Space

    __slots__ = ["v_function", "state_space"]

    def extract(self) -> ConditionalEquation:
        return ConditionalEquation(
            space=self.state_space,
            equation=self.v_function,
            condition_type=EquationConditionType.GREATER_THAN_OR_EQUAL,
            condition_value=0
        )


@dataclass
class InitialLessThanOneConstraint(Constraint):
    """
    forall x ∈ X_{initial} → 1 - V(x) ≥ 0
    """
    v_function: Equation
    initial_state_space: Space

    __slots__ = ["v_function", "initial_state_space"]

    def extract(self) -> ConditionalEquation:
        # _monomial_one = Equation.extract_equation_from_string("1")
        _monomial_one = Equation(
            monomials=[
                Monomial(
                    coefficient=1,
                    variable_generators=[],
                    power=[],
                )
            ]
        )
        _eq = _monomial_one.sub(self.v_function)
        return ConditionalEquation(
            space=self.initial_state_space,
            equation=_eq,
            condition_type=EquationConditionType.GREATER_THAN_OR_EQUAL,
            condition_value=0
        )


@dataclass
class SafetyConstraint(Constraint):
    """
    forall x ∈ X_{unsafe} → V(x) - 1/(1-p) ≥ 0
    """
    v_function: Equation
    unsafe_state_space: Space
    probability_threshold: float

    __slots__ = ["v_function", "unsafe_state_space", "probability_threshold"]

    def extract(self) -> ConditionalEquation:
        p = self.probability_threshold
        _eq = Equation.extract_equation_from_string(f"1/(1-{p})")
        _eq = self.v_function.sub(_eq)
        return ConditionalEquation(
            space=self.unsafe_state_space,
            equation=_eq,
            condition_type=EquationConditionType.GREATER_THAN_OR_EQUAL,
            condition_value=0,
        )


@dataclass
class DecreaseExpectationConstraint(Constraint):
    """
    forall x ∈ X → V(x) − E[V(x_{k+1}) | x_{k} = x] − ϵ ≥ 0

    Please note that for the Expectation of Disturbance, we assume that the disturbance is one dimensional.
    """
    v_function: Equation
    state_space: Space
    target_state_space: Space
    current_state: SystemState  # TODO: check what is our current state
    action_policy: SystemControlPolicy
    system_dynamics: SystemDynamics
    system_disturbance: SystemStochasticNoise
    maximal_equation_degree: int
    epsilon: float

    __slots__ = [
        "v_function", "state_space", "target_state_space", "current_state", "action_policy",
        "system_dynamics", "system_disturbance", "maximal_equation_degree", "epsilon"
    ]

    def extract(self) -> ConditionalEquation:
        _next_expected_State = self.system_dynamics(
            state=self.current_state,
            action=self.action_policy(self.current_state),
            noise=None,
            evaluate=False,
        )
        _eq_epsilon = Equation.extract_equation_from_string(str(self.epsilon))
        _ns_args = _next_expected_State()
        _v_next = self.v_function(**_ns_args)
        disturbance_expectations = self.system_disturbance.get_expectations(self.maximal_equation_degree)
        _Dim = 1 # As we assumed that we only have one dimension of disturbance TODO: fix this assumption
        _v_next.replace(" ", "")
        refined_disturbance_expectations = {
            f"D{_Dim}**{i}": d for i, d in enumerate(disturbance_expectations, start=1)
        }
        refined_disturbance_expectations[f"D{_Dim}"] = disturbance_expectations[0]
        # _v_next = _replace_keys_with_values(_v_next, refined_disturbance_expectations)

        _eq = Equation.extract_equation_from_string(_v_next)
        _eq.add(_eq_epsilon)
        _eq = self.v_function.sub(_eq)

        # TODO: Calculate X/Xt space


        return ConditionalEquation(
            space=self.state_space, # todo: incorrect, fix it
            equation=_eq,
            condition_type=EquationConditionType.GREATER_THAN_OR_EQUAL,
            condition_value=0
        )
