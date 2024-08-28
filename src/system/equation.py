from dataclasses import dataclass, field
from numbers import Number
from typing import Sequence


_to_power = lambda v, p: f"{v}**{p}" if p != 1 else str(v)


@dataclass
class Monomial:
    symbolic_coefficient: str
    variable_generators: Sequence[str]
    power: Sequence[Number]
    coefficient: Number = 0
    is_coefficient_known: field(init=False) = False

    def coefficient_known(self) -> bool:
        return self.is_coefficient_known

    def set_coefficient_value(self, value: float) -> None:
        self.coefficient = value
        self.is_coefficient_known = True

    def __str__(self) -> str:
        _coefficients = str(self.coefficient) if self.coefficient_known() else self.symbolic_coefficient

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

    def __call__(self, *args, **kwargs):
        _eq = str(self)
        for k, v in kwargs.items():
            _eq = _eq.replace(k, str(v))
        _eq_v = eval(_eq)
        return _eq_v
