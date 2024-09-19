from dataclasses import dataclass
from numbers import Number
from typing import Sequence

import sympy as sp
from sympy import expand
from sympy.parsing.sympy_parser import parse_expr

from . import logger


_to_power = lambda v, p: f"{v}**{p}" if p != 1 else str(v)
# __max_float_digits__ = 20


def _smt_preorder_var_pow_helper(_var, _pow) -> str:
    """
    Converts {var}^{pow} to a preorder multiplication.
    """
    if _pow == 0:
        return "1"
    if _pow == 1:
        return _var
    if _pow == 2:
        return f"(* {_var} {_var})"
    return f"(* {_smt_preorder_var_pow_helper(_var, _pow // 2)} {_smt_preorder_var_pow_helper(_var, (_pow + 1) // 2)})"

@dataclass
class Monomial:
    coefficient: float
    variable_generators: Sequence[str]
    power: Sequence[float]

    __slots__ = ["coefficient", "variable_generators", "power"]

    def __post_init__(self):
        if len(self.variable_generators) != len(self.power):
            logger.error(f"The number of variables and powers must match: {self.variable_generators} vs. {self.power}")
            raise ValueError(f"The number of variables and powers must match: {self.variable_generators} vs. {self.power}")
        if self.coefficient == 0:
            self.variable_generators, self.power = [], []
            self.coefficient = 0
            return

        filtered = [(v, p) for v, p in zip(self.variable_generators, self.power) if p != 0]
        if not filtered:
            self.variable_generators, self.power = [], []
            return
        self.variable_generators, self.power = zip(*filtered)
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

    def is_zero(self) -> bool:
        return self.coefficient == 0

    def is_numeric(self) -> bool:
        return len(self.variable_generators) == 0

    def to_smt_preorder(self) -> str:
        if self.coefficient == 0:
            return "0"
        coefficient_var_pow = str(self.coefficient)
        # coefficient_var_pow = str(round(self.coefficient, __max_float_digits__))
        if len(self.variable_generators) == 0:
            return coefficient_var_pow
        for v, p in zip(self.variable_generators, self.power):
            coefficient_var_pow = f"(* {coefficient_var_pow} {_smt_preorder_var_pow_helper(v, p)})"
        return coefficient_var_pow

    def __str__(self) -> str:
        if self.coefficient == 0:
            return "0"
        coefficient_var_pow = str(self.coefficient)
        # coefficient_var_pow = str(round(self.coefficient, __max_float_digits__))
        if len(self.variable_generators) == 0:
            return coefficient_var_pow
        if self.coefficient == 1:
            return f"{' * '.join([_to_power(v, p) for v, p in zip(self.variable_generators, self.power) if p != 0])}"
        return f"{coefficient_var_pow} * {' * '.join([_to_power(v, p) for v, p in zip(self.variable_generators, self.power) if p != 0])}" # .replace(" * 1", "")




class PolynomialParser:

    @staticmethod
    def extraxt_monomials_from_string(polynomial: str) -> list[Monomial]:
        expanded = expand(polynomial)
        expr = parse_expr(str(expanded))
        if expr.is_number:
            return [Monomial(coefficient=expr, variable_generators=[], power=[])]
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
