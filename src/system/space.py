from functools import lru_cache

from .polynomial.equation import Equation
from .polynomial.inequality import Inequality, EquationConditionType


_fix_comparators = lambda s: s.replace(" ", "") \
    .replace(">=", ">").replace("<=", "<") \
    .replace(">", ">=").replace("<", "<=")
_find_first_comparator = lambda s: min(
    (s.find(op) for op in ["<=", ">="] if s.find(op) != -1),
    default=-1
)


def _process_space_inequalities(inequality: str) -> list[Inequality]:
    """
    Processes an inequality string of the form "bound [>= or <=] {equation} [<= or >=] bound".
    Only supports two comparators per expression, and bounds should be numeric.
    """
    inequality = _fix_comparators(inequality)
    comparator_count = inequality.count(">=") + inequality.count("<=")
    if comparator_count == 0:
        raise ValueError(f"Invalid inequality format (zero-comparator): {inequality}")
    if comparator_count > 2:
        raise ValueError(f"Invalid inequality format (multi-comparator): {inequality}")

    # Find the first comparator and split the inequality
    first_idx = _find_first_comparator(inequality)
    operand1, operator1, remaining = (
        inequality[:first_idx],
        inequality[first_idx:first_idx + 2],
        inequality[first_idx + 2:]
    )

    # If there's only one comparator, return a single Inequality instance
    if comparator_count == 1:
        return [
            Inequality(
                left_equation=Equation.extract_equation_from_string(operand1),
                inequality_type=EquationConditionType.extract_from_string(operator1),
                right_equation=Equation.extract_equation_from_string(remaining)
            )
        ]

    # For two comparators, process the second part
    second_idx = _find_first_comparator(remaining)
    operand2, operator2, operand3 = (
        remaining[:second_idx],
        remaining[second_idx:second_idx + 2],
        remaining[second_idx + 2:]
    )

    return [
        Inequality(
            left_equation=Equation.extract_equation_from_string(operand1),
            inequality_type=EquationConditionType.extract_from_string(operator1),
            right_equation=Equation.extract_equation_from_string(operand2)
        ),
        Inequality(
            left_equation=Equation.extract_equation_from_string(operand2),
            inequality_type=EquationConditionType.extract_from_string(operator2),
            right_equation=Equation.extract_equation_from_string(operand3)
        )
    ]

@lru_cache(maxsize=32)
def extract_space_inequalities(string: str) -> list[Inequality]:
    string = (string.replace("OR", "or").replace("AND", "and").
              replace("&", "and").replace("|", "or"))
    return [
        p_ineq
        for _ieq in string.split("and")
        for p_ineq in _process_space_inequalities(_ieq)
    ]
