from dataclasses import dataclass
from enum import Enum

from . import logger
from .equation import Equation


class EquationConditionType(Enum):
    EQUAL = "=="
    Not_EQUAL = "!="
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_THAN_OR_EQUAL = ">="
    LESS_THAN_OR_EQUAL = "<="

    __slots__ = []

    @classmethod
    def extract_from_string(cls, string):
        string = string.strip()
        for condition in cls:
            if condition.value == string:
                return condition
        raise ValueError(f"Invalid condition type: {string}")

    @staticmethod
    def neggate_condition(condition):
        if condition == EquationConditionType.GREATER_THAN:
            return EquationConditionType.LESS_THAN_OR_EQUAL
        if condition == EquationConditionType.GREATER_THAN_OR_EQUAL:
            return EquationConditionType.LESS_THAN
        if condition == EquationConditionType.LESS_THAN:
            return EquationConditionType.GREATER_THAN_OR_EQUAL
        if condition == EquationConditionType.LESS_THAN_OR_EQUAL:
            return EquationConditionType.GREATER_THAN
        if condition == EquationConditionType.EQUAL:
            return EquationConditionType.Not_EQUAL
        if condition == EquationConditionType.Not_EQUAL:
            return EquationConditionType.EQUAL
        return condition

    @staticmethod
    def relax_condition(condition):
        if condition == EquationConditionType.GREATER_THAN:
            return EquationConditionType.GREATER_THAN_OR_EQUAL
        if condition == EquationConditionType.LESS_THAN:
            return EquationConditionType.LESS_THAN_OR_EQUAL
        return condition

    @staticmethod
    def mirror_condition(condition):
        if condition == EquationConditionType.GREATER_THAN_OR_EQUAL:
            return EquationConditionType.LESS_THAN_OR_EQUAL
        if condition == EquationConditionType.LESS_THAN_OR_EQUAL:
            return EquationConditionType.GREATER_THAN_OR_EQUAL
        if condition == EquationConditionType.GREATER_THAN:
            return EquationConditionType.LESS_THAN
        if condition == EquationConditionType.LESS_THAN:
            return EquationConditionType.GREATER_THAN
        return condition


@dataclass
class Inequality:
    left_equation: Equation
    inequality_type: EquationConditionType
    right_equation: Equation

    __slots__ = ["left_equation", "inequality_type", "right_equation"]

    def __post_init__(self):
        if self.inequality_type not in EquationConditionType:
            raise ValueError(f"Invalid inequality type: {self.inequality_type}")

        if self.inequality_type not in [EquationConditionType.LESS_THAN_OR_EQUAL, EquationConditionType.GREATER_THAN_OR_EQUAL]:
            logger.warning(f"You may use '>=' or '<=' for more efficiency. Currently, we are relaxing the condition be default.")
            self.inequality_type = EquationConditionType.relax_condition(self.inequality_type)
        self._normalize()

    def _normalize(self):
        if self.inequality_type in [EquationConditionType.LESS_THAN, EquationConditionType.LESS_THAN_OR_EQUAL]:
            self.left_equation, self.right_equation = self.right_equation, self.left_equation
            self.inequality_type = EquationConditionType.mirror_condition(self.inequality_type)
        if not self.right_equation.is_zero():
            self.left_equation = self.left_equation.sub(self.right_equation)
            self.right_equation = Equation.extract_equation_from_string("0")

    def neggate(self):
        return Inequality(
            left_equation=self.left_equation,
            inequality_type=EquationConditionType.neggate_condition(self.inequality_type),
            right_equation=self.right_equation,
        )

    def to_smt_preorder(self):
        return f"({self.inequality_type.value} {self.left_equation.to_smt_preorder()} {self.right_equation.to_smt_preorder()})"

    def __eq__(self, other):
        if not isinstance(other, Inequality):
            return False
        return str(self) == str(other)

    def __hash__(self):
        return hash(str(self))

    def to_detailed_string(self) -> str:
        return f"{self.left_equation} {self.inequality_type.value} {self.right_equation}"

    def __str__(self) -> str:
        if len(self.left_equation.monomials) > 1:
            lhs = "LHS"
        else:
            lhs = str(self.left_equation)
        if len(self.right_equation.monomials) > 1:
            rhs = "RHS"
        else:
            rhs = str(self.right_equation)
        return f"{lhs} {self.inequality_type.value} {rhs}"


