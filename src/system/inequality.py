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


@dataclass
class Inequality:
    left_equation: Equation
    inequality_type: EquationConditionType
    right_equation: Equation

    __slots__ = ["left_equation", "inequality_type", "right_equation"]

    def __post_init__(self):
        if self.inequality_type not in EquationConditionType:
            raise ValueError(f"Invalid inequality type: {self.inequality_type}")
        # if self.bound != 0:
        #     logger.warning(f"You may use 0 bounded for more efficiency")
        # else:
        #     self.bound = 0

        if self.inequality_type not in [EquationConditionType.LESS_THAN_OR_EQUAL, EquationConditionType.GREATER_THAN_OR_EQUAL]:
            logger.warning(f"You may use '>=' or '<=' for more efficiency")
        if self.inequality_type in [EquationConditionType.LESS_THAN, EquationConditionType.LESS_THAN_OR_EQUAL]:
            self.left_equation, self.right_equation = self.right_equation, self.left_equation
            self.inequality_type = EquationConditionType.GREATER_THAN_OR_EQUAL if self.inequality_type == EquationConditionType.LESS_THAN_OR_EQUAL else EquationConditionType.GREATER_THAN

        if not self.right_equation.is_zero():
            logger.warning(f"Right equation is not zero: {self.right_equation}. Fixing the equation")
            self.left_equation = self.left_equation.sub(self.right_equation)
            self.right_equation = Equation.extract_equation_from_string("0")

    def __str__(self) -> str:
        return f"{self.left_equation} {self.inequality_type.value} {self.right_equation}"


