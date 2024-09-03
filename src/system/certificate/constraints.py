from abc import ABC, abstractmethod
from dataclasses import dataclass

from ..equation import Equation
from ..space import Space


class Constraint(ABC):

    @abstractmethod
    def extract(self):
        pass


@dataclass
class NonNegativityConstraint(Constraint):
    """
    forall x ∈ X → V(x) ≥ 0
    """
    RASM_function: Equation
    state_space: Space

    def extract(self):
        pass


@dataclass
class InitialLessThanOneConstraint(Constraint):
    """
    forall x ∈ X_{initial} → 1 - V(x) ≥ 0
    """
    RASM_function: Equation
    initial_state_space: Space

    def extract(self):
        pass


@dataclass
class SafetyConstraint(Constraint):
    """
    forall x ∈ X_{unsafe} → V(x) - 1/(1-p) ≥ 0
    """
    RASM_function: Equation
    unsafe_state_space: Space
    probability_threshold: float

    def extract(self):
        pass


@dataclass
class DecreaseExpectationConstraint(Constraint):
    """
    forall x ∈ X → V(x) − E[V(x_{k+1}) | x_{k} = x] − ϵ ≥ 0
    """
    RASM_function: Equation
    state_space: Space
    target_state_space: Space
    next_state_equation: Equation
    disturbance_distribution_expectations: list[float]
    epsilon: float

    def extract(self):
        pass


