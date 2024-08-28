from dataclasses import dataclass
from numbers import Number
from typing import Sequence


_to_power = lambda v, p: f"{v}**{p}" if p != 1 else str(v)


class Monomial:
    symbolic_coefficient: str
    variable_generators: Sequence[str]
    power: Sequence[Number]
    coefficient: Number = 0
    __is_coefficient_known: bool = False

    def is_coefficient_known(self) -> bool:
        return self.__is_coefficient_known
    def set_coefficient_value(self, value: float) -> None:
        self.coefficient = value
        self.__is_coefficient_known = True

    def __str__(self) -> str:
        if self.is_coefficient_known():
            _coefficients = str(self.coefficient)
        else:
            _coefficients = self.symbolic_coefficient

        _variables = [_to_power(v, p) for v, p in zip(self.variable_generators, self.power)]

        return f"({_coefficients} * {' * '.join(_variables)})"


@dataclass
class Equation:
    """"
    Each equation is a sequence of monomials, summing together to form a polynomial.
    """
    monomials: Sequence[Monomial]

    def __str__(self) -> str:
        return " + ".join([str(m) for m in self.monomials])