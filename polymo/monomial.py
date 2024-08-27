from copy import deepcopy
from dataclasses import dataclass
from typing import List, Union, Generator

from polymo import logger
from polymo.polynomial import Polynomial
from polymo.symbolicM import SymbolicMonomial
from polymo.symbolicP import SymbolicPolynomial


@dataclass
class Monomial:

    var_generators: List[str]  # var_generators is a list of variable generators
    constant: float            # constant is a real valued constant of the monomial
    powers: List[int]          # powers is a list of powers of each variable  TODO: Should I consider float power?

    def __post_init__(self):
        if self.constant == 0:
            logger.warning("Monomial constant is 0, ignoring powers")
            self.powers = [0] * len(self.var_generators)
        else:
            self.powers = [int(_pow) for _pow in self.powers]

        if len(self.powers) < len(self.var_generators):
            logger.warning(f"Powers and var_generators have different lengths, using power 1 to match generators ({len(self.powers)} < {len(self.var_generators)})")
            self.powers += [1] * (len(self.var_generators) - len(self.powers))
        elif len(self.powers) > len(self.var_generators):
            logger.warning(f"Powers and var_generators have different lengths, truncating powers to match generators ({len(self.powers)} > {len(self.var_generators)})")
            self.powers = self.powers[:len(self.var_generators)]

        # Returns a monomial of the form constant * var^var_power

    @classmethod
    def single_var_of_power(cls, var_generators, var, var_power, constant=1):
        assert (var in var_generators), f"Variable -{var}- is not in var_generators list"
        index = var_generators.index(var)

        powers = [0] * len(var_generators)
        powers[index] = var_power

        return Monomial(var_generators, constant, powers)

    def get_constant(self) -> float:
        return self.constant

    def get_powers(self, as_str=False) -> Union[List[int], List[str]]:
        if as_str:
            return [str(power) for power in self.powers]
        return self.powers

    def get_var_generators(self) -> List[str]:
        return self.var_generators

    def get_copy(self) -> "Monomial":
        return Monomial(deepcopy(self.var_generators), self.constant, deepcopy(self.powers))

    # Increase the constant of the monomial by const
    def increase_constant_by(self, const: float):
        self.constant = self.constant + const

    # Multiplies the constant of the monomial by const
    def multiply_by_constant(self, const: float):
        self.constant = self.constant * const

    # Multiplication with another monomial
    def multiply_by_monomial(self, monomial: "Monomial"):
        assert self.var_generators == monomial.get_var_generators(), \
            f"Variable generators do not match ({self.var_generators} != {monomial.get_var_generators()})"

        self.constant *= monomial.get_constant()
        self.powers = [self_p + mono_p for self_p, mono_p in zip(self.powers, monomial.get_powers())]

    # Substitutes value for the variable var
    def replace_var_by_value(self, var: str, value: float):
        assert var in self.var_generators, f"Variable -{var}- is not in variable generators"
        index = self.var_generators.index(var)

        power = self.powers[index]
        self.powers[index] = 0
        self.constant = self.constant * pow(value, power)

    # Returns a zero monomial
    @classmethod
    def zero_monomial(cls, var_generators: List[str]) -> "Monomial":
        powers = [0] * len(var_generators)
        return Monomial(var_generators=var_generators, constant=0, powers=powers)

    # Returns a unit monomial
    @classmethod
    def one_monomial(cls, var_generators: List[str]) -> "Monomial":
        powers = [0] * len(var_generators)
        return Monomial(var_generators=var_generators, constant=1, powers=powers)

    def substitute_var_by_poly(self, var: str, polynomial: Polynomial) -> Polynomial:
        assert (self.var_generators == polynomial.get_var_generators()), f"Variable generators do not match ({self.var_generators} != {polynomial.get_var_generators()})"
        assert (var in self.var_generators), f"Variable -{var}- is not in variable generators"
        polynomial = polynomial.get_copy()

        new_poly = Polynomial.one_polynomial(self.var_generators)
        new_poly.multiply_by_const(self.constant)
        for var_gen, power in zip(self.var_generators, self.powers):
            if var_gen != var:
                new_poly.multiply_by_monomial(
                    Monomial.single_var_of_power(self.var_generators, var_gen, power))
                continue
            for _ in range(power):
                new_poly.multiply_by_polynomial(polynomial)
        return new_poly

    def total_degree(self) -> int:
        return sum(self.powers)

    def substitute_var_by_symbol(self, var: str, symbol: str) -> SymbolicPolynomial: # TODO: check for probable bugs
        assert var in self.var_generators, f"Variable -{var}- is not in variable generators"
        monomial = Monomial.one_monomial(self.var_generators)

        for var_gen, power in zip(self.var_generators, self.powers):
            if var_gen != var:
                monomial.multiply_by_monomial(Monomial.single_var_of_power(self.var_generators, var_gen, power))

        constant = str(self.constant)
        index = self.var_generators.index(var)
        if self.powers[index] >= 2:
            constant += f" * {symbol}^{self.powers[index]}"
        elif self.powers[index] == 1:
            constant += f" * {symbol}"

        return SymbolicPolynomial(
            self.var_generators, {SymbolicMonomial(self.var_generators, constant, monomial.get_powers())}
        )

    def substitute_var_by_symbol_simultaneous(self, updates: dict) -> SymbolicPolynomial:
        monomial = Monomial.one_monomial(self.var_generators)
        for var_gen, power in zip(self.var_generators, self.powers):
            if var_gen not in updates:
                monomial.multiply_by_monomial(Monomial.single_var_of_power(self.var_generators, var_gen, power))

        constant = str(self.constant)
        powers = monomial.get_powers()
        for var, symbol in updates.items():
            index = self.var_generators.index(var)
            if self.powers[index] >= 2:
                constant += f"*{symbol}**{self.powers[index]}"
            elif self.powers[index] == 1:
                constant += f"*{symbol}"

        return SymbolicPolynomial(self.var_generators, {SymbolicMonomial(self.var_generators, constant, powers)})

    def __str__(self):
        if self.constant == 0:
            return "0"

        synthesized_str = str(self.constant)
        for var_gen, power in zip(self.var_generators, self.powers):
            term_repr = f" * {var_gen}"
            if power >= 2:
                term_repr = f" * {var_gen}^{power}"
            synthesized_str += term_repr

        return synthesized_str
