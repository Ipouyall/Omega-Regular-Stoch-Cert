from dataclasses import dataclass, field
from numbers import Number
from typing import Sequence, List

from polymo import logger

_to_power = lambda v, p: f"{v}**{p}" if p != 1 else str(v)


@dataclass
class Monomial:
    symbolic_coefficient: str
    variable_generators: Sequence[str]
    power: Sequence[Number]
    coefficient: Number = 0
    is_coefficient_known: bool = field(init=False, default=False)

    def known_coefficient(self) -> bool:
        return self.is_coefficient_known

    def set_coefficient_value(self, value: float) -> None:
        self.coefficient = value
        self.is_coefficient_known = True

    def __eq__(self, other):
        if not isinstance(other, Monomial):
            return False
        if len(self.variable_generators) != len(other.variable_generators):
            return False
        vp = {v: p for v, p in zip(self.variable_generators, self.power)}
        o_vp = {v: p for v, p in zip(other.variable_generators, other.power)}

        return vp == o_vp

    @classmethod
    def _add_coefficients(cls, self, other):
        if self == other:
            _coefficient1 = self.coefficient if self.known_coefficient() else self.symbolic_coefficient
            _coefficient2 = other.coefficient if other.known_coefficient() else other.symbolic_coefficient
            if not other.known_coefficient():
                _coefficient = f"{_coefficient1} + {_coefficient2}"
            elif other.coefficient > 0:
                _coefficient = f"{_coefficient1} + {_coefficient2}"
            elif other.coefficient < 0:
                _coefficient = f"{_coefficient1} - {abs(_coefficient2)}"
            else:
                logger.warning(f"Cannot add Monomial with coefficient {other.coefficient}")
                return NotImplemented
            _monomial = Monomial(_coefficient, self.variable_generators, self.power)
            return _monomial
        logger.warning(f"Cannot add Monomial with {other}")
        return NotImplemented

    def __add__(self, other):
        if not isinstance(other, Monomial):
            logger.warning(f"Cannot add Monomial with {type(other)}")
            return NotImplemented
        return self._add_coefficients(self, other)

    def __iadd__(self, other):
        if not isinstance(other, Monomial):
            logger.warning(f"Cannot add Monomial with {type(other)}")
            return NotImplemented
        return self._add_coefficients(self, other)

    def __str__(self) -> str:
        _coefficients = str(self.coefficient) if self.known_coefficient() else self.symbolic_coefficient

        _variables = [_to_power(v, p) for v, p in zip(self.variable_generators, self.power) if p != 0]
        if len(_variables) == 0:
            return f"({_coefficients})"

        if not self.known_coefficient() and ("+" in _coefficients or "-" in _coefficients):
            _coefficients = f"({_coefficients})"
        return f"({_coefficients} * {' * '.join(_variables)})"


@dataclass
class Equation:
    """"
    Each equation is a sequence of monomials, summing together to form a polynomial.
    """
    monomials: List[Monomial] = field(default_factory=list)

    def add_monomial(self, monomial: Monomial) -> None: # TODO: not an efficient way!
        if monomial not in self.monomials:
            self.monomials.append(monomial)
            return
        idx = self.monomials.index(monomial)
        self.monomials[idx] = self.monomials[idx] + monomial


    def __str__(self) -> str:
        return " + ".join([str(m) for m in self.monomials])

    def __call__(self, *args, **kwargs):
        _eq = str(self)
        for k, v in kwargs.items():
            _eq = _eq.replace(k, str(v))
        _eq_v = eval(_eq)
        return _eq_v
