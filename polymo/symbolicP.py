from copy import deepcopy
from dataclasses import dataclass
from typing import List, Set, Union

from polymo.symbolicM import SymbolicMonomial


@dataclass
class SymbolicPolynomial:
    var_generators: List[str]        # var_generators is a list of variable generators
    monomials: Set[SymbolicMonomial] # monomials is a set of symbolic monomials

    @classmethod
    def zero_polynomial(cls, var_generators: List[str]) -> "SymbolicPolynomial":
        return SymbolicPolynomial(var_generators, {SymbolicMonomial.zero_monomial(var_generators)})

    @classmethod
    def one_polynomial(cls, var_generators):
        return SymbolicPolynomial(var_generators, {SymbolicMonomial.one_monomial(var_generators)})

    @classmethod
    def single_var_of_power(cls, var_generators: List[str], var: str, power: str,
                            constant: str = "1") -> "SymbolicPolynomial":
        monomial = SymbolicMonomial.single_var_of_power(var_generators, var, constant, power)
        return SymbolicPolynomial(var_generators, {monomial})

    @classmethod
    def constant_poly(cls, var_generators: List[str], constant: str) -> "SymbolicPolynomial":
        powers = ["0"] * len(var_generators)
        mono = SymbolicMonomial(var_generators, constant, powers)
        return SymbolicPolynomial(var_generators, {mono})

    def get_monomials(self) -> Set[SymbolicMonomial]:
        return self.monomials

    def get_var_generators(self) -> List[str]:
        return self.var_generators

    def get_copy(self) -> "SymbolicPolynomial":
        _monomials = {monomial.get_copy() for monomial in self.monomials}
        var_generators = deepcopy(self.var_generators)
        return SymbolicPolynomial(var_generators, _monomials)

    def negate_polynomial(self):
        for monomial in self.monomials:
            monomial.negate_monomial()

    def add_monomial(self, monomial: SymbolicMonomial):
        assert self.var_generators == monomial.get_var_generators(), f"Variable generators do not match ({self.var_generators} != {monomial.get_var_generators()})"
        monomial = monomial.get_copy()
        for mono in self.monomials:
            if monomial.get_powers() == mono.get_powers():
                mono.add_to_constant(monomial.get_constant(as_int=False))
                break
        else:
            self.monomials.add(monomial)

    def add_polynomial(self, polynomial: "SymbolicPolynomial"):
        assert self.var_generators == polynomial.get_var_generators(), f"Variable generators do not match ({self.var_generators} != {polynomial.get_var_generators()})"
        for monomial in polynomial.get_copy().get_monomials():
            self.add_monomial(monomial)

    def substitute_var_by_poly(self, var: str, polynomial: "SymbolicPolynomial") -> "SymbolicPolynomial":
        assert self.var_generators == polynomial.get_var_generators(), f"Variable generators do not match ({self.var_generators} != {polynomial.get_var_generators()})"
        assert var in self.var_generators, f"Variable -{var}- is not in var_generators list"

        new_poly = SymbolicPolynomial.zero_polynomial(self.var_generators)
        for monomial in self.monomials:
            substitute = monomial.substitute_var_by_poly(var, polynomial)
            new_poly.add_polynomial(substitute)
        return new_poly

    def substitute_var_by_poly_simultaneous(self, updates: dict) -> "SymbolicPolynomial":
        new_poly = SymbolicPolynomial.zero_polynomial(self.var_generators)
        for monomial in self.monomials:
            substitute = monomial.substitute_var_by_poly_simultaneous(updates)
            new_poly.add_polynomial(substitute)
        return new_poly

    def total_degree(self) -> int:
        return max(monomial.total_degree() for monomial in self.monomials)

    def coefficient_of_monomial(self, powers: List[str], as_int: bool = False) -> Union[int, float, None]:
        for monomial in self.monomials:
            if monomial.get_powers(as_int=False) == powers:
                return monomial.get_constant(as_int=as_int)
        return None

    def substitute_var_by_symbol(self, var: str, symbol: str) -> "SymbolicPolynomial":
        assert var in self.var_generators, f"Variable -{var}- is not in var_generators list"
        new_poly = SymbolicPolynomial.zero_polynomial(self.var_generators)
        for monomial in self.monomials:
            substitute = monomial.substitute_var_by_symbol(var, symbol)
            new_poly.add_polynomial(substitute)
        return new_poly

    def substitute_vars_by_symbols_simultaneous(self, updates: dict) -> "SymbolicPolynomial":
        for var in updates:
            assert var in self.var_generators, f"Variable -{var}- is not in var_generators list"
        new_poly = SymbolicPolynomial.zero_polynomial(self.var_generators)
        for monomial in self.monomials:
            substitute = monomial.substitute_var_by_symbol_simultaneous(updates)
            new_poly.add_polynomial(substitute)
        return new_poly

    def __str__(self):
        string = ""
        for i, monomial in enumerate(self.monomials):
            if monomial.get_constant()[0] == "-":
                string += str(monomial)
            else:
                string += (" + " if i > 0 else "") + str(monomial)
        return string
