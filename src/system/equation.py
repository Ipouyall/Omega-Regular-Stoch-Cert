from dataclasses import dataclass, field
from numbers import Number
from typing import Sequence, List, Optional

from . import logger

_to_power = lambda v, p: f"{v}**{p}" if p != 1 else str(v)


@dataclass
class Monomial:
    symbolic_coefficient: str
    variable_generators: Sequence[str]
    power: Sequence[Number]
    coefficient: Optional[float] = field(init=False, default=None)
    is_coefficient_known: bool = field(init=False, default=False)

    def __post_init__(self):
        if len(self.variable_generators) != len(self.power):
            logger.error(f"The number of variables and powers must match: {self.variable_generators} vs. {self.power}")
            raise ValueError(f"The number of variables and powers must match: {self.variable_generators} vs. {self.power}")
        if len(self.symbolic_coefficient) == 0:
            logger.warning("Empty coefficient provided, setting it to 1")
            self.symbolic_coefficient = "1"
        if self.symbolic_coefficient.isnumeric():
            self.coefficient = float(self.symbolic_coefficient)
        if self.coefficient is not None:
            self.is_coefficient_known = True

        _coefficient_refined = self.symbolic_coefficient.replace("(", "").replace(")", "").replace(" ", "")
        self.symbolic_coefficient = _coefficient_refined.replace("+-", "-")

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
                _coefficient = f"{_coefficient1} + {_coefficient2}" if _coefficient2[0] != "-" else f"{_coefficient1} + ({_coefficient2})"
            elif other.coefficient > 0:
                _coefficient = f"{_coefficient1} + {_coefficient2}"
            elif other.coefficient < 0:
                _coefficient = f"{_coefficient1} + (-{abs(_coefficient2)})"
            else:
                logger.warning(f"Cannot add Monomial with coefficient {other.coefficient}")
                return NotImplemented
            return Monomial(_coefficient, self.variable_generators, self.power)
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

    @classmethod
    def extract_monomial_from_string(cls, monomial: str) -> "Monomial":
        """
        The input expected to be as examples below:
        Simple: {one non-negative or symbolic constant} * {variable1} ** {power1} * {variable2} ** {power2} * ... >> 2 * x ** 2 * y ** 3
        For negative constants:

        """
        monomial = monomial.strip().replace(" ", "")
        if len(monomial) == 0:
            return Monomial("1", [], [])
        while True:
            if monomial[0] == "(" and monomial[-1] == ")":
                monomial = monomial[1:-1]
            else:
                break
        if "*" not in monomial:
            return cls(monomial, [], [])
        monomial = monomial.replace("**", "^")
        monomial_parts = monomial.split("*")
        _constant, var_pow = monomial_parts[0], monomial_parts[1:]
        _variables = []
        _powers = []
        for vp in var_pow:
            if "^" in vp:
                v, p = vp.split("^")
                _variables.append(v)
                _powers.append(int(p))
            else:
                _variables.append(vp)
                _powers.append(1)
        return cls(_constant, _variables, _powers)


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

    def __call__(self, **kwargs):
        _eq = str(self)
        for k, v in kwargs.items():
            if str(v)[0] == "-":
                _eq = _eq.replace(k, f"({v})")
            else:
                _eq = _eq.replace(k, f"{v}")
        if kwargs.get("evaluate", False):
            _eq = eval(_eq)
        return _eq

    @classmethod
    def extract_equation_from_string(cls, equation: str) -> "Equation":  # TODO: may fix this later to accept subtractions
        """
        The input expected to be as examples below:
        Simple: {monomial1} + {monomial2} + ...
        Please note that there should be no space inside each monomial and monomials are seperated as " + ", note that negate the constant for subtraction
        """
        equation = equation.strip()
        if len(equation) == 0:
            return Equation([])
        equation_parts = equation.split(" + ")
        _monomials = [Monomial.extract_monomial_from_string(m) for m in equation_parts]
        return cls(_monomials)