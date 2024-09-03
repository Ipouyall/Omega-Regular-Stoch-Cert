from dataclasses import dataclass, field
from typing import List

from .polynomial import Monomial, PolynomialParser


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
