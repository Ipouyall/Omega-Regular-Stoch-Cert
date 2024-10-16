from copy import deepcopy
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
        if monomial.is_zero():
            return
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

    def is_numeric(self) -> bool:
        return len(self.monomials) == 1 and all([m.is_numeric() for m in self.monomials])

    def is_zero(self) -> bool:
        return all([m.coefficient == 0 for m in self.monomials]) or len(self.monomials) == 0

    def __str__(self) -> str:
        if len(self.monomials) == 0:
            return "0"
        return " + ".join([f"({m})" for m in self.monomials])

    def to_smt_preorder(self) -> str:
        if self.is_zero():
            return "0"
        eq = self.monomials[0].to_smt_preorder()
        for m in self.monomials[1:]:
            eq = f"(+ {eq} {m.to_smt_preorder()})"
        return eq

    def __call__(self, **kwargs) -> str:
        _eq = str(self)
        for k, v in kwargs.items():
            _eq = _eq.replace(k, f"({v})")
        return _eq

    @classmethod
    def extract_equation_from_string(cls, equation: str) -> "Equation":
        monomials = PolynomialParser.extraxt_monomials_from_string(equation)
        monomials = [m for m in monomials if m.coefficient != 0]
        return cls(monomials=monomials)
