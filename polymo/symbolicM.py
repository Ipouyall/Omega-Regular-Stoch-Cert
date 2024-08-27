from copy import deepcopy
from dataclasses import dataclass
from typing import List, Union

from polymo import logger
from polymo.monomial import Monomial
from polymo.polynomial import Polynomial
from polymo.symbolicP import SymbolicPolynomial


@dataclass
class SymbolicMonomial:

    var_generators: List[str] # var_generators is a list of variable generators
    constant: str             # symbolic constant, given by a string
    powers: List[str]         # powers is a list of powers of each variable

    # Returns a monomial of the form constant * var^var_power
    @classmethod
    def single_var_of_power(cls, var_generators: List[str], var: str, constant: str = "1",
                            var_power: str = "1") -> "SymbolicMonomial":
        assert (var in var_generators), f"Variable -{var}- is not in var_generators list"
        index = var_generators.index(var)

        powers = ["0"] * len(var_generators)
        powers[index] = var_power

        return SymbolicMonomial(var_generators, constant, powers)

    def get_copy(self) -> "SymbolicMonomial":
        return SymbolicMonomial(deepcopy(self.var_generators), self.constant, deepcopy(self.powers))

    # Returns a zero monomial
    @classmethod
    def zero_monomial(cls, var_generators: List[str]) -> "SymbolicMonomial":
        constant = "0"
        powers = ["0"] * len(var_generators)
        return SymbolicMonomial(var_generators, constant, powers)

    # Returns a unit monomial
    @classmethod
    def one_monomial(cls, var_generators: List[str]) -> "SymbolicMonomial":
        constant = "1"
        powers = ["0"] * len(var_generators)
        return SymbolicMonomial(var_generators, constant, powers)


    def __post_init__(self):
        if self.constant == "0":
            self.powers = ["0"] * len(self.var_generators)
        else:
            self.powers = [str(_pow).strip() for _pow in self.powers]

        if len(self.powers) < len(self.var_generators):
            logger.warning(f"Powers and var_generators have different lengths, using power 1 to match generators ({len(self.powers)} < {len(self.var_generators)})")
            self.powers += ["1"] * (len(self.var_generators) - len(self.powers))  # TODO: check whether to add 0 or 1 as default?
        elif len(self.powers) > len(self.var_generators):
            logger.warning(f"Powers and var_generators have different lengths, truncating powers to match generators ({len(self.powers)} > {len(self.var_generators)})")
            self.powers = self.powers[:len(self.var_generators)]

        if self.constant is None or self.constant == "":
            self.constant = "0"
            logger.warning("Constant isn't provided, setting to 0")

        logger.debug(f"Monomial created as -> {self}")

    def get_constant(self, as_int : bool = False) -> Union[int, str]:
        if as_int:
            return int(self.constant)
        return self.constant

    def get_powers(self, as_int : bool = False) -> List[Union[int, str]]:
        if as_int:
            return [int(power) for power in self.powers]
        return self.powers

    def get_var_generators(self) -> List[str]:
        return self.var_generators

    def substitute_var_by_poly(self, var, polynomial):
        assert (self.var_generators == polynomial.get_var_generators())
        assert (var in self.var_generators)
        polynomial = polynomial.get_copy()
        index_of_var = self.var_generators.index(var)
        power_of_var = int(self.powers[index_of_var])
        # replacement_poly is defined as polynomial^power_of_var
        replacement_poly = Polynomial.one_polynomial(self.var_generators)
        for _ in range(power_of_var):
            replacement_poly.multiply_by_polynomial(polynomial)
        # to avoid numerical errors
        # replacement_poly.remove_zeros()
        # now multiply replacement_poly by the remaining variables of monomial
        for i in range(len(self.var_generators)):
            if self.var_generators[i] != var:
                mono = Monomial.single_var_of_power(self.var_generators, self.var_generators[i], self.get_powers()[i])
                replacement_poly.multiply_by_monomial(mono)
        # create a symbolic polynomial from replacement_poly by multiplying each constant by the symbolic constant of the monomial
        symbolic_poly_monomials = set()
        for monomial in replacement_poly.get_monomials():
            powers = deepcopy(monomial.get_powers())
            constant = monomial.get_constant()
            symbolic_poly_monomials.add(
                SymbolicMonomial(self.var_generators, str(constant) + "*" + self.constant, powers))
        return SymbolicPolynomial(self.var_generators, symbolic_poly_monomials)

    def substitute_var_by_poly_simultaneous(self, updates):
        replacement_poly = Polynomial.one_polynomial(self.var_generators)
        # multiply replacement_poly by the variables of monomial that are not updated
        for i in range(len(self.var_generators)):
            if self.var_generators[i] not in updates:
                mono = Monomial.single_var_of_power(self.var_generators, self.var_generators[i], self.get_powers()[i])
                replacement_poly.multiply_by_monomial(mono)
        for var in updates:
            index_of_var = self.var_generators.index(var)
            polynomial = updates[var].get_copy()
            for _ in range(int(self.powers[index_of_var])):
                replacement_poly.multiply_by_polynomial(polynomial)
        # create a symbolic polynomial from replacement_poly by multiplying each constant by the symbolic constant of the monomial
        symbolic_poly_monomials = set()
        for monomial in replacement_poly.get_monomials():
            powers = deepcopy(monomial.get_powers())
            constant = monomial.get_constant()
            if constant != "0":
                symbolic_poly_monomials.add(
                    SymbolicMonomial(self.var_generators, str(constant) + "*" + self.constant, powers))
        return SymbolicPolynomial(self.var_generators, symbolic_poly_monomials)

    def add_to_constant(self, string: str):
        self.constant = f"{self.constant} + ({string})"

    def total_degree(self) -> int:
        return sum((int(p) for p in self.powers))

    def negate_monomial(self):
        self.constant = self.constant[1:] if self.constant[0] == "-" else "-" + self.constant
        # self.constant = "-1*(" + self.constant + ")"

    def substitute_var_by_symbol(self, var: str, symbol: str) -> SymbolicPolynomial:
        assert var in self.var_generators, f"Variable -{var}- is not in var_generators list"
        monomial = Monomial.one_monomial(self.var_generators)
        for i, var_gen in enumerate(self.var_generators):
            if var_gen != var:
                monomial.multiply_by_monomial(
                    Monomial.single_var_of_power(self.var_generators, var_gen, self.powers[i])
                )
        constant = f"({self.constant})"
        powers = monomial.get_powers()
        index = self.var_generators.index(var)
        if int(self.powers[index]) >= 2:
            constant += f" * {symbol}^{self.powers[index]}"
        elif self.powers[index] == "1":
            constant += f" * {symbol}"
        return SymbolicPolynomial(self.var_generators, {SymbolicMonomial(self.var_generators, constant, powers)})

    def substitute_var_by_symbol_simultaneous(self, updates: dict[str, str]) -> SymbolicPolynomial:
        monomial = Monomial.one_monomial(self.var_generators)
        for i in range(len(self.var_generators)):
            if self.var_generators[i] not in updates:
                monomial.multiply_by_monomial(
                    Monomial.single_var_of_power(self.var_generators, self.var_generators[i], self.powers[i])
                )
        constant = self.constant
        powers = monomial.get_powers(as_str=True)
        for var in updates:
            index = self.var_generators.index(var)
            if int(self.powers[index]) >= 2:
                constant = constant + "*" + updates[var] + "**" + str(self.powers[index])
            elif int(self.powers[index]) == 1:
                constant = constant + "*" + updates[var]
        return SymbolicPolynomial(self.var_generators, {SymbolicMonomial(self.var_generators, constant, powers)})

    def __str__(self):
        string = f"{self.constant}"
        if "*" in string:
            string = f"({self.constant})"

        for var, power in zip(self.var_generators, self.powers):
            if power >= 2:
                string += f" * {var}^{power}"
            elif power == 1:
                string += f" * {var}"
        return string
