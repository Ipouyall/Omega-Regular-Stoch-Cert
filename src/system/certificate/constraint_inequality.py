from dataclasses import dataclass
from typing import Union, Optional

from src.system.polynomial.inequality import Inequality

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
    lhs:  Union[Inequality|list[Inequality]|None]
    rhs: Union[Inequality|list[Inequality]|None]
    aggregation_type: Optional[str] = "conjunction"

    __operation_to_symbol = {
        "conjunction": ("and", "&"),
        "disjunction": ("or", "|"),
    }

    def __post_init__(self):
        if self.lhs is None and self.rhs is None:
            raise ValueError("At least one of the left-hand side or right-hand side must be provided.")
        if self.lhs is not None and self.rhs is None:
            self.rhs = self.lhs
            self.lhs = None

    @staticmethod
    def _list_to_smt_preorder(ineq: list[Inequality], aggregation_type) -> str:
        _str = ineq[0].to_smt_preorder()
        for ieq in ineq[1:]:
            _str = f"({ConstraintInequality.__operation_to_symbol[aggregation_type][0]} {_str} {ieq.to_smt_preorder()})"
        return _str

    @staticmethod
    def _none_to_smt_preorder() -> str:
        """Returns and always true inequality"""
        return "(> 1 0)"

    @staticmethod
    def _inequality_to_smt_preorder(ineq: Inequality) -> str:
        return ineq.to_smt_preorder()

    @staticmethod
    def _to_smt_preorder_helper(inequality: Union[Inequality|list[Inequality]|None], aggregation_type) -> str:
        if inequality is None:
            return ConstraintInequality._none_to_smt_preorder()
        if isinstance(inequality, list):
            return ConstraintInequality._list_to_smt_preorder(inequality, aggregation_type)
        return ConstraintInequality._inequality_to_smt_preorder(inequality)

    def to_polyhorn_preorder(self, aggregation_type) -> str:
        _variables = " ".join(f"({v} Real)" for v in self.variables)
        _lhs = self._to_smt_preorder_helper(self.lhs, aggregation_type)
        _rhs = self._to_smt_preorder_helper(self.rhs, aggregation_type)

        return f"(assert (forall ({_variables}) (=> {_lhs} {_rhs})))"

    @staticmethod
    def _hand_side_to_str(hand_side: Union[Inequality | list[Inequality] | None], aggregation_type) -> Union[str|None]:
        if hand_side is None:
            return None
        if isinstance(hand_side, list):
            if len(hand_side) > 4:
                return f"({hand_side[0]}) {ConstraintInequality.__operation_to_symbol[aggregation_type][1]} ..+{len(hand_side)-2}.. {ConstraintInequality.__operation_to_symbol[aggregation_type][1]} ({hand_side[-1]})"
            return f" {ConstraintInequality.__operation_to_symbol[aggregation_type][1]} ".join(f"({ineq})" for ineq in hand_side)
        return f"({hand_side})"

    def __str__(self):
        if len(self.variables) > 3:
            _variables = f"({self.variables[0]} Real) ..+{len(self.variables)-2}.. ({self.variables[-1]} Real)"
        else:
            _variables = ", ".join(f"({v} Real)" for v in self.variables)
        _lhs = self._hand_side_to_str(self.lhs, self.aggregation_type)
        _rhs = self._hand_side_to_str(self.rhs, self.aggregation_type)

        if _lhs is None and _rhs is None:
            return "Not defined"
        if _lhs is None:
            return f"FORALL: {_variables}  THEN: {_rhs}"
        return f"FORALL: {_variables}  IF: {_lhs}  THEN: {_rhs}"
