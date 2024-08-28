from copy import deepcopy
from dataclasses import dataclass
from typing import List, Set, Union

from polymo.monomial import Monomial
from polymo.symbolicP import SymbolicPolynomial


@dataclass
class Polynomial:
    var_generators: List[str]  # var_generators is a list of variable generators
    monomials: Set[Monomial]  # monomials is a set of monomials

    @classmethod
    def zero_polynomial(cls, var_generators) -> "Polynomial":
        monomials = set()
        monomials.add(Monomial.zero_monomial(var_generators))
        return Polynomial(var_generators, monomials)

    @classmethod
    def one_polynomial(cls, var_generators: List[str]) -> "Polynomial":
        return Polynomial(var_generators, {Monomial.one_monomial(var_generators)})

    @classmethod
    def single_var_of_power(cls, var_generators, var, power, constant=1) -> "Polynomial":
        monomial = Monomial.single_var_of_power(var_generators, var, power, constant)
        return Polynomial(var_generators, {monomial})

    def get_monomials(self) -> Set[Monomial]:
        return self.monomials

    def get_var_generators(self) -> List[str]:
        return self.var_generators

    def get_copy(self) -> "Polynomial":
        _monomials = {monomial.get_copy() for monomial in self.monomials}
        var_generators = deepcopy(self.var_generators)
        return Polynomial(var_generators, _monomials)

    def remove_zeros(self, threshold: float = 1e-7):
        self.monomials = {
            monomial for monomial in self.monomials
            if abs(monomial.get_constant()) >= threshold
        }
        if not self.monomials:
            self.monomials.add(Monomial.zero_monomial(self.var_generators))

    def negate_polynomial(self):
        for monomial in self.monomials:
            monomial.multiply_by_constant(-1)

    def multiply_by_const(self, const: Union[int, float]):
        for monomial in self.monomials:
            monomial.multiply_by_constant(const)

    def add_monomial(self, monomial: Monomial):
        assert self.var_generators == monomial.get_var_generators(), f"Variable generators do not match ({self.var_generators} != {monomial.get_var_generators()})"
        monomial = monomial.get_copy()

        for mono in self.monomials: # TODO: check if it can be problematic: (I) all instanced of the polynomial may not have one shared address, (II) generators' order matter
            if monomial.get_powers() == mono.get_powers():
                mono.increase_constant_by(monomial.get_constant())
                break
        else:
            self.monomials.add(monomial)

    def add_polynomial(self, polynomial: "Polynomial"):
        assert self.var_generators == polynomial.get_var_generators(), f"Variable generators do not match ({self.var_generators} != {polynomial.get_var_generators()})"
        for monomial in polynomial.get_copy().get_monomials():
            self.add_monomial(monomial)

    def multiply_by_monomial(self, monomial: Monomial):
        assert self.var_generators == monomial.get_var_generators(), f"Variable generators do not match ({self.var_generators} != {monomial.get_var_generators()})"
        for mono in self.monomials:
            mono.multiply_by_monomial(monomial)

    def multiply_by_polynomial(self, polynomial: "Polynomial"):
        assert self.var_generators == polynomial.get_var_generators(), f"Variable generators do not match ({self.var_generators} != {polynomial.get_var_generators()})"
        product = Polynomial.zero_polynomial(self.var_generators)
        for monomial in polynomial.get_monomials():
            temp_poly_term = self.get_copy()
            temp_poly_term.multiply_by_monomial(monomial)
            product.add_polynomial(temp_poly_term)
        self.monomials = product.get_monomials()
        # self.remove_zeros()

    def substitute_var_by_poly(self, var: str, polynomial: "Polynomial") -> "Polynomial":
        assert self.var_generators == polynomial.get_var_generators(), "Variable generators do not match"
        assert var in self.var_generators, f"Variable -{var}- is not found in {self.var_generators}"
        new_poly = Polynomial.zero_polynomial(self.var_generators)
        for monomial in self.monomials:
            new_poly.add_polynomial(monomial.substitute_var_by_poly(var, polynomial.get_copy()))
            # new_poly.remove_zeros()
        return new_poly

    def total_degree(self) -> int:
        return max(monomial.total_degree() for monomial in self.monomials)

    def coefficient_of_monomial(self, powers: List[int]) -> Union[int, float, None]:
        for monomial in self.monomials:
            if monomial.get_powers() == powers:
                return monomial.get_constant()
        return None

    def substitute_var_by_symbol(self, var: str, symbol: str) -> SymbolicPolynomial:
        assert var in self.var_generators, f"Variable -{var}- is not in var_generators list"
        new_poly = SymbolicPolynomial.zero_polynomial(self.var_generators)
        for monomial in self.monomials:
            new_poly.add_polynomial(monomial.substitute_var_by_symbol(var, symbol))
        return new_poly

    def substitute_vars_by_symbols_simultaneous(self, updates: dict) -> SymbolicPolynomial:
        for var in updates:
            assert var in self.var_generators, f"Variable -{var}- is not in var_generators list"
        new_poly = SymbolicPolynomial.zero_polynomial(self.var_generators)
        for monomial in self.monomials:
            substitute = monomial.substitute_var_by_symbol_simultaneous(updates)
            new_poly.add_polynomial(substitute)
        return new_poly

    def __str__(self):
        string = ""
        not_first = False
        # will be used to store the constant monomial since we want to print it last (a requirement of Sting)
        constant_monomial = None
        for monomial in self.monomials:
            if monomial.total_degree() == 0:
                constant_monomial = monomial.get_copy()
            elif monomial.get_constant() < 0:
                string += str(monomial)
                not_first = True
            elif monomial.get_constant() > 0:
                if not_first is False:
                    string += str(monomial)
                else:
                    string += f" + {monomial}"
                not_first = True
        # now print constant monomial if found
        if constant_monomial is None:
            pass
        elif constant_monomial.get_constant() < 0:
            string += str(constant_monomial)
        elif constant_monomial.get_constant() > 0:
            string += str(constant_monomial) if not_first else f" + {constant_monomial}"

        return string or "0"
