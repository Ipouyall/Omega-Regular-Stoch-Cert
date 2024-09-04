from dataclasses import dataclass, field
from numbers import Number
from typing import Sequence, Optional

import sympy as sp
from sympy.parsing.sympy_parser import parse_expr

from . import logger


_to_power = lambda v, p: f"{v}**{p}" if p != 1 else str(v)


@dataclass
class Coefficient:
    symbol: str
    value: Optional[float] = field(init=False, default=None)

    def __post_init__(self):
        if len(self.symbol) == 0:
            logger.warning("Empty coefficient provided, setting it to 1")
            self.symbol = "1"
        if self.symbol.isnumeric():
            self.value = float(self.symbol)

    def is_known(self) -> bool:
        return self.value is not None

    def _add_two_coefficients(self, other):
        if self.is_known() and other.is_known():
            return Coefficient(str(self.value + other.value))
        return Coefficient(f"{self.symbol}+{other.symbol}")

    def _add_coefficient_and_number(self, other):
        if self.is_known():
            return Coefficient(str(self.value + other))
        return Coefficient(f"{self.symbol}+{other}")

    def _add_coefficient_and_symbol(self, other):
        if self.is_known():
            return Coefficient(f"{self.value}+{other}")
        return Coefficient(f"{self.symbol}+{other}")

    def _add(self, other):
        if isinstance(other, Coefficient):
            return self._add_two_coefficients(other)
        if isinstance(other, (int, float)):
            return self._add_coefficient_and_number(other)
        if isinstance(other, str):
            return self._add_coefficient_and_symbol(other)
        logger.warning(f"Cannot add Coefficient with {other} of type {type(other)}")
        return NotImplemented

    def set_value(self, key: str, value: float) -> None:
        self.symbol = self.symbol.replace(key, str(value))



    def __str__(self):
        return str(self.value) if self.is_known() else self.symbol

    def __eq__(self, other):
        if not isinstance(other, Coefficient):
            return False
        return self.value == other.value if self.is_known() and other.is_known() else self.symbol == other.symbol

    def __add__(self, other):
        return self._add(other)

    def __iadd__(self, other):
        ns = self._add(other)
        if ns is not NotImplemented:
            self.symbol = ns.symbol
            self.value = ns.value
        return self


@dataclass
class Monomial:
    coefficient: float
    variable_generators: Sequence[str]
    power: Sequence[Number]

    __slots__ = ["coefficient", "variable_generators", "power"]

    def __post_init__(self):
        if len(self.variable_generators) != len(self.power):
            logger.error(f"The number of variables and powers must match: {self.variable_generators} vs. {self.power}")
            raise ValueError(f"The number of variables and powers must match: {self.variable_generators} vs. {self.power}")
        # if not isinstance(self.coefficient, Coefficient):
        #     self.coefficient = Coefficient(str(self.coefficient))

        # sort variable_generators and their respective powers
        self.variable_generators, self.power = zip(*sorted(zip(self.variable_generators, self.power), key=lambda x: x[0]))

    def __eq__(self, other):
        """
        We assume two monomials are equal if they have the same variables and powers. Although this is not the right definition, and we should take coefficients into account, it is sufficient for our purposes.
        """
        if not isinstance(other, Monomial):
            return False
        if len(self.variable_generators) != len(other.variable_generators):
            return False
        for (_sv, _sp), (_ov, _op) in zip(zip(self.variable_generators, self.power), zip(other.variable_generators, other.power)):
            if _sv != _ov or _sp != _op:
                return False
        return True

    def add(self, other):
        """
        Adds two monomials if possible, otherwise returns None.
        """
        if not self == other:
            return None
        return Monomial(
            coefficient=self.coefficient + other.coefficient,
            variable_generators=self.variable_generators,
            power=self.power
        )

    def negate(self):
        return Monomial(
            coefficient=-self.coefficient,
            variable_generators=self.variable_generators,
            power=self.power
        )

    def __str__(self) -> str:
        if self.coefficient == 1:
            return f"{' * '.join([_to_power(v, p) for v, p in zip(self.variable_generators, self.power) if p != 0])}"
        return f"{self.coefficient} * {' * '.join([_to_power(v, p) for v, p in zip(self.variable_generators, self.power) if p != 0])}" # .replace(" * 1", "")




class PolynomialParser:

    @staticmethod
    def extraxt_monomials_from_string(polynomial: str) -> list[Monomial]:
        expr = parse_expr(polynomial)
        sympy_polynomial = sp.Poly(expr)
        return PolynomialParser._convert_sympy_polynomial_to_monomials(sympy_polynomial)



    @staticmethod
    def _convert_sympy_polynomial_to_monomials(sympy_polynomial: sp.Poly) -> list[Monomial]:
        variable_generators = [
            str(var)
            for var in list(sympy_polynomial.gens)
        ]
        sympy_monomials = sympy_polynomial.monoms()
        sympy_coefficients = sympy_polynomial.coeffs()

        return [
            Monomial(
                coefficient=coefficient,
                variable_generators=variable_generators,
                power=monomial
            )
            for coefficient, monomial in zip(sympy_coefficients, sympy_monomials)
        ]
