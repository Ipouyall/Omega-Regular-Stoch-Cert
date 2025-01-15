from dataclasses import dataclass
from functools import lru_cache
from typing import Union, Optional

from sympy.physics.units import newton

from ..polynomial.inequality import Inequality
from .utils import infix_to_prefix
from ..space import extract_space_inequalities


class ConstraintAggregationType:
    CONJUNCTION = "conjunction" # and
    DISJUNCTION = "disjunction" # or


operation_to_symbol = {
    "conjunction": ("and", "&"),
    "disjunction": ("or", "|"),
}

bool_to_smt_bool = {
    "|": "or",
    "&": "and",
}

_zero_to_ten = "0123456789"
_ten_chars = "abcdefghij"
_translation_table = str.maketrans(_zero_to_ten, _ten_chars)

def _list_to_smt_preorder(ineq: list[Inequality], aggregation_type: ConstraintAggregationType) -> str:
    _str = ineq[0].to_smt_preorder()
    for ieq in ineq[1:]:
        _str = f"({operation_to_symbol[aggregation_type][0]} {_str} {ieq.to_smt_preorder()})"
    return _str


def _single_to_smt_preorder(ineq: Inequality) -> str:
    return ineq.to_smt_preorder()


def _to_smt_preorder_helper(inequality: Union[Inequality|list[Inequality]|None], aggregation_type: ConstraintAggregationType) -> Union[str|None]:
    if inequality is None:
        return None
    if isinstance(inequality, list):
        return _list_to_smt_preorder(inequality, aggregation_type)
    return _single_to_smt_preorder(inequality)


@lru_cache(maxsize=64)
def _guard_lookup_to_preorder_helper(preposition, label) -> dict[str, str]:
    return {
        f"!{preposition}": _to_smt_preorder_helper(
            inequality=[_eq.neggate() for _eq in extract_space_inequalities(label)],
            aggregation_type=ConstraintAggregationType.DISJUNCTION
        ),
        f"{preposition}": _to_smt_preorder_helper(
            inequality=extract_space_inequalities(label),
            aggregation_type=ConstraintAggregationType.CONJUNCTION
        )
    }

def _guard_lookup_to_preorder(lookup_table: dict[str, str]) -> dict[str, str]:
    new_table = {}
    for key, value in lookup_table.items():
        new_table.update(_guard_lookup_to_preorder_helper(key, value))
    return new_table


@dataclass
class Guard:
    guard: str
    lookup_table: dict[str, str]

    def to_smt_preorder(self) -> str:
        if not self.guard:
            return "(> 1 0)"
        preorder = infix_to_prefix(self.guard).replace(" ", "")
        preorder = preorder.translate(_translation_table)
        _to_smt = _guard_lookup_to_preorder(self.lookup_table)
        for key, value in _to_smt.items():
            key = key.translate(_translation_table)
            preorder = preorder.replace(f"({key})", value)
            preorder = preorder.replace(key, value)
        for sign, translation in bool_to_smt_bool.items():
            preorder = preorder.replace(sign, translation)
        if preorder.startswith("((") and preorder.endswith("))"):
            return preorder[1:-1]
        return preorder

    def is_guarded(self) -> bool:
        return True if self.guard else False

    def to_detailed_str(self):
        return f"({self.guard})"

    def __str__(self):
        if self.is_guarded():
            return "Guard-δ"
        return ""


@dataclass
class GuardedInequality:
    inequality: Union[Inequality|list[Inequality]]
    guard: Union[Guard|str]
    aggregation_type: ConstraintAggregationType = ConstraintAggregationType.CONJUNCTION
    lookup_table: Optional[dict[str, str]] = None

    def __post_init__(self):
        if isinstance(self.guard, str) and self.lookup_table is None:
            raise ValueError("You should provide lookup table for the string guard.")
        elif isinstance(self.guard, str):
            self.guard = Guard(self.guard, self.lookup_table)

    def to_smt_preorder(self) -> str:
        return f"(and {self.guard.to_smt_preorder()} {_to_smt_preorder_helper(self.inequality, self.aggregation_type)})"

    @staticmethod
    def hand_side_to_str(guard: Guard, inequality: Union[Inequality|list[Inequality]], aggregation_type) -> str:
        if isinstance(inequality, list):
            if len(inequality) > 2:
                return f"{guard} & ({inequality[0]}) {operation_to_symbol[aggregation_type][1]} ..+{len(inequality) - 2}.. {operation_to_symbol[aggregation_type][1]} ({inequality[-1]})"
            return f"{guard} & " f" {operation_to_symbol[aggregation_type][1]} ".join(
                f"({ineq})" for ineq in inequality)
        return f"{guard} & ({inequality })"

    def to_detailed_string(self):
        if not self.guard.is_guarded():
            return SubConstraint.expression_to_str(self.inequality, self.aggregation_type)
        if isinstance(self.inequality, list):
            return f"{self.guard.to_detailed_str()} & (" + f" {operation_to_symbol[self.aggregation_type][1]} ".join(
                f"({ineq.to_detailed_string()})" for ineq in self.inequality) + ')'
        return f"{self.guard.to_detailed_str()} & ({self.inequality.to_detailed_string()})"

    def __str__(self):
        if not self.guard.is_guarded():
            return SubConstraint.expression_to_str(self.inequality, self.aggregation_type)
        return self.hand_side_to_str(self.guard, self.inequality, self.aggregation_type)


@dataclass
class SubConstraint:
    expr_1: Union[Inequality|list[Inequality]|GuardedInequality|list[GuardedInequality]|None] = None
    expr_2: Union[Inequality|list[Inequality]|GuardedInequality|list[GuardedInequality]|None] = None
    aggregation_type: ConstraintAggregationType = None

    def __post_init__(self):
        if self.expr_1 is None and self.expr_2 is None:
            raise ValueError("You should provide at least one expression.")
        if self.aggregation_type is None and (isinstance(self.expr_1, list) or isinstance(self.expr_2, list)):
            raise ValueError("Aggregation type must be provided for list of expressions.")

    def to_smt_preorder(self) -> str:
        _expr1 = _to_smt_preorder_helper(self.expr_1, self.aggregation_type)
        _expr2 = _to_smt_preorder_helper(self.expr_2, self.aggregation_type)

        if _expr1 is not None and _expr2 is not None:
            return f"({operation_to_symbol[self.aggregation_type][0]} {_expr1} {_expr2})"
        if _expr1 is None:
            return f"{_expr2}"
        return f"{_expr1}"

    @staticmethod
    def expression_to_str(expression: Union[Inequality|list[Inequality]|None], aggregation_type: ConstraintAggregationType, detailed: bool = False) -> Union[str|None]:
        if expression is None:
            return None
        if not isinstance(expression, list):
            return f"{expression.to_detailed_string()}" if detailed else str(expression)
        join_str = f" {operation_to_symbol[aggregation_type][1]} "
        if detailed:
            return join_str.join(f"({ineq.to_detailed_string()})" for ineq in expression)
        if len(expression) > 3:
            return f"({expression[0]}){join_str}..+{len(expression) - 2}..{join_str}({expression[-1]})"
        return join_str.join(f"({ineq})" for ineq in expression)


    def to_detailed_string(self):
        _expr1 = self.expression_to_str(self.expr_1, self.aggregation_type, detailed=True)
        _expr2 = self.expression_to_str(self.expr_2, self.aggregation_type, detailed=True)

        if _expr1 and _expr2:
            return f"({_expr1} {operation_to_symbol[self.aggregation_type][1]} {_expr2})"
        return _expr1 or _expr2

    def __str__(self):
        _expr1 = self.expression_to_str(self.expr_1, self.aggregation_type)
        _expr2 = self.expression_to_str(self.expr_2, self.aggregation_type)

        if _expr1 is not None and _expr2 is not None:
            return f"({_expr1} {operation_to_symbol[self.aggregation_type][1]} {_expr2})"
        if _expr1 is None:
            return f"{_expr2}"
        return f"{_expr1}"


@dataclass
class ConstraintInequality:
    """
    Lists are treated as 'and' conditions.
    You cannot have both left-hand side and right-hand side as None.
    If you provide:
        (I) both sides, it will be treated as implication,
        (II) only one side, it will be treated as the main inequality,

    aggregation_type: conjunction|disjunction
    """
    variables: list[str]
    lhs: Union[SubConstraint|None] = None
    rhs: Union[SubConstraint|None] = None

    def __post_init__(self):
        if self.lhs is None and self.rhs is None:
            raise ValueError("At least one of the left-hand side or right-hand side must be provided.")
        if self.lhs is not None and self.rhs is None:
            self.rhs = self.lhs
            self.lhs = None

    @staticmethod
    def _none_to_smt_preorder() -> str:
        """Returns and always true inequality"""
        return "(> 1 0)"

    @staticmethod
    def _sub_to_smt_preorder(ineq: SubConstraint) -> str:
        return ineq.to_smt_preorder()

    @staticmethod
    def _to_smt_preorder_helper(inequality: Union[SubConstraint|None]) -> str:
        if inequality is None:
            return ConstraintInequality._none_to_smt_preorder()
        return inequality.to_smt_preorder()

    def to_polyhorn_preorder(self) -> str:
        _variables = " ".join(f"({v} Real)" for v in self.variables)
        _lhs = self._to_smt_preorder_helper(self.lhs)
        _rhs = self._to_smt_preorder_helper(self.rhs)

        return f"(assert (forall ({_variables}) (=> {_lhs} {_rhs})))"

    @staticmethod
    def _hand_side_to_str(hand_side: Union[SubConstraint|None], detailed: bool = False) -> Union[str|None]:
        if hand_side is None:
            return None
        if detailed:
            return hand_side.to_detailed_string()
        return f"{hand_side}"

    def to_detail_string(self):
        _variables = " ".join(f"({v} Real)" for v in self.variables)
        _lhs = self._hand_side_to_str(hand_side=self.lhs, detailed=True)
        _rhs = self._hand_side_to_str(hand_side=self.rhs, detailed=True)

        if _lhs is None and _rhs is None:
            return "Not defined"
        if _lhs is None:
            return f"FORALL: {_variables}  THEN: {_rhs}"
        return f"FORALL: {_variables}  IF: {_lhs}  THEN: {_rhs}"

    def __str__(self):
        if len(self.variables) > 3:
            _variables = f"({self.variables[0]} Real) ..+{len(self.variables)-2}.. ({self.variables[-1]} Real)"
        else:
            _variables = ", ".join(f"({v} Real)" for v in self.variables)
        _lhs = self._hand_side_to_str(self.lhs)
        _rhs = self._hand_side_to_str(self.rhs)

        if _lhs is None and _rhs is None:
            return "Not defined"
        if _lhs is None:
            return f"FORALL: {_variables}  THEN: {_rhs}"
        return f"FORALL: {_variables}  IF: {_lhs}  THEN: {_rhs}"
