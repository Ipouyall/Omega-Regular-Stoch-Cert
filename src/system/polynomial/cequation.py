from dataclasses import dataclass

from .equation import Equation
from .inequality import Inequality


# @dataclass
# class ConditionalEquation:
#     condition: list[Inequality]
#     equation: Equation
#
#     def add_monomial(self, monomial: "Monomial") -> None:
#         if monomial.is_zero():
#             return
#         self.equation.add_monomial(monomial)
#
#     def negate(self) -> None:
#         for i in range(len(self.equation.monomials)):
#             self.equation.monomials[i] = self.equation.monomials[i].negate()
#
#     def add(self, other: "ConditionalEquation|Equation") -> "ConditionalEquation":
#         if isinstance(other, Equation):
#             _eq = self.equation.add(other)
#         elif isinstance(other, ConditionalEquation):
#             _eq = self.equation.add(other.equation)
#         else:
#             raise TypeError(f"Expected Equation or ConditionalEquation, got {type(other)}")
#         return ConditionalEquation(condition=self.condition, equation=_eq)
#
#     def sub(self, other: "ConditionalEquation|Equation") -> "ConditionalEquation":
#         if isinstance(other, Equation):
#             _eq = self.equation.sub(other)
#         elif isinstance(other, ConditionalEquation):
#             _eq = self.equation.sub(other.equation)
#         else:
#             raise TypeError(f"Expected Equation or ConditionalEquation, got {type(other)}")
#         return ConditionalEquation(condition=self.condition, equation=_eq)
#
#     def is_numeric(self) -> bool:
#         return self.equation.is_numeric()
#
#     def is_zero(self) -> bool:
#         return self.equation.is_zero()
#
#     def __str__(self) -> str:
#         if len(self.condition) == 0:
#             return str(self.equation)
#         return f"{' & '.join([str(c) for c in self.condition])} => {self.equation}"
#
#     # def to_smt_preorder(self) -> str:
#     #     if self.is_zero():
#     #         return "0"
#     #     eq = self.monomials[0].to_smt_preorder()
#     #     for m in self.monomials[1:]:
#     #         eq = f"(+ {eq} {m.to_smt_preorder()})"
#     #     return eq
#
#     # @classmethod
#     # def extract_equation_from_string(cls, equation: str) -> "Equation":
#     #     monomials = PolynomialParser.extraxt_monomials_from_string(equation)
#     #     monomials = [m for m in monomials if m.coefficient != 0]
#     #     return cls(monomials=monomials)
