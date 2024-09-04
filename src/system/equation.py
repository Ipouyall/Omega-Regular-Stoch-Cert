from copy import deepcopy
from dataclasses import dataclass, field
from typing import List
from enum import Enum

from . import logger
from .polynomial import Monomial, PolynomialParser
from .space import Space


@dataclass
class Equation:
    """"
    Each equation is a sequence of monomials, summing together to form a polynomial.
    """
    monomials: List[Monomial] = field(default_factory=list)

    def add_monomial(self, monomial: Monomial) -> None:
        for i in range(len(self.monomials)):
            _add = self.monomials[i].add(monomial)
            if _add is not None:
                self.monomials[i] = _add
                return
        self.monomials.append(monomial)

    def negate(self) -> None:
        for i in range(len(self.monomials)):
            self.monomials[i] = self.monomials[i].negate()

    def add(self, other: "Equation") -> "Equation":
        if not isinstance(other, Equation):
            raise TypeError(f"Expected Equation, got {type(other)}")
        new_equation = deepcopy(self)
        for monomial in other.monomials:
            new_equation.add_monomial(monomial)
        return new_equation

    def sub(self, other: "Equation") -> "Equation":
        if not isinstance(other, Equation):
            raise TypeError(f"Expected Equation, got {type(other)}")
        new_equation = deepcopy(self)
        for monomial in other.monomials:
            new_equation.add_monomial(monomial.negate())
        return new_equation

    def __str__(self) -> str:
        return " + ".join([f"({m})" for m in self.monomials])

    def __call__(self, **kwargs):
        _eq = str(self)
        for k, v in kwargs.items():
            _eq = _eq.replace(k, f"({v})")
        if kwargs.get("evaluate", False):
            _eq = eval(_eq)
        return _eq

    @classmethod
    def extract_equation_from_string(cls, equation: str) -> "Equation":
        monomials = PolynomialParser.extraxt_monomials_from_string(equation)
        return cls(monomials=monomials)


class EquationConditionType(Enum):
    EQUAL = "=="
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_THAN_OR_EQUAL = ">="
    LESS_THAN_OR_EQUAL = "<="

    __slots__ = []


@dataclass
class ConditionalEquation:
    space: Space
    equation: Equation
    condition_type: EquationConditionType
    condition_value: float

    def __post_init__(self):
        for attr_name, attr_type in self.__annotations__.items():
            attr_value = getattr(self, attr_name)
            if not isinstance(attr_value, attr_type):
                raise TypeError(
                    f"Attribute '{attr_name}' is expected to be of type {attr_type}, but got {type(attr_value)} instead."
                )
        if self.condition_type not in EquationConditionType:
            raise ValueError(f"Invalid condition type: {self.condition_type}")
        if self.condition_value != 0:
            logger.warning(f"Condition value is not zero: {self.condition_value}")
        else:
            self.condition_value = 0

    def __str__(self) -> str:
        return f"""for {self.space.get_inequalities()} : {self.equation} {self.condition_type.value} {self.condition_value}"""

