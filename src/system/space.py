from dataclasses import dataclass, field

from .equation import Equation
from .inequality import Inequality, EquationConditionType


def _process_space_inequalities(inequality: str) -> list[Inequality]:
    """
    the inequality could be in format of "bound [>= or <=] {equation} [<= or >=] bound" this means we cannot have more than two comparator in one run.
    It doesn't support comparing two variable-generators (bounds should be numerix)
    """
    find_first_com = lambda s: s.find(">=") if ">=" in s else s.find("<=")
    counts = inequality.count(">=") + inequality.count("<=")
    if counts == 0:
        raise ValueError(f"Invalid inequality format (zero-comparator): {inequality}")
    if counts > 2:
        raise ValueError(f"Invalid inequality format (multi-comparator): {inequality}")
    has_two_bounds = counts == 2

    first_inequality_index = find_first_com(inequality)

    _operand1, _operator1, inequality = (inequality[:first_inequality_index],
                                        inequality[first_inequality_index: first_inequality_index + 2],
                                        inequality[first_inequality_index + 2:])
    if not has_two_bounds:
        return [
            Inequality(
                left_equation=Equation.extract_equation_from_string(_operand1),
                inequality_type=EquationConditionType.extract_from_string(_operator1),
                right_equation=Equation.extract_equation_from_string(inequality)
            )
        ]
    second_inequality_index = find_first_com(inequality)
    _operand2, _operator2, _operand3 = (inequality[:second_inequality_index],
                                        inequality[second_inequality_index: second_inequality_index + 2],
                                        inequality[second_inequality_index + 2:])
    return [
        Inequality(
            left_equation=Equation.extract_equation_from_string(_operand1),
            inequality_type=EquationConditionType.extract_from_string(_operator1),
            right_equation=Equation.extract_equation_from_string(_operand2)
        ),
        Inequality(
            left_equation=Equation.extract_equation_from_string(_operand2),
            inequality_type=EquationConditionType.extract_from_string(_operator2),
            right_equation=Equation.extract_equation_from_string(_operand3)
        )
    ]


@dataclass
class Space:
    """
    Each inequality defines boundaries one of the dimensions of the state space.
    """
    dimension: int
    inequalities: str
    listed_space_inequalities: list[Inequality] = field(init=False, default=None)

    def __post_init__(self):
        if not isinstance(self.inequalities, str):
            raise TypeError("inequalities must be a string")
        if self.dimension <= 0:
            raise ValueError("dimension must be a positive integer")

        self.inequalities = self.inequalities.replace(" ", "")\
            .replace("OR", "or").replace("AND", "and")

        if "or" in self.inequalities:
            raise ValueError("OR is not supported in the current version")

    def get_inequalities(self):
        return self.inequalities

    def _extract_inequalities(self) -> list[Inequality]:
        _inequalities = self.inequalities.split("and")
        _fix_comparators = lambda s: s.replace(" ", "").replace(">=", ">").replace("<=", "<")\
            .replace(">", ">=").replace("<", "<=")
        return [
            p_ineq
            for _ieq in _inequalities
            for p_ineq in _process_space_inequalities(_fix_comparators(_ieq))
        ]

    def get_space_inequalities(self) -> list[Inequality]:
        if self.listed_space_inequalities is None:
            self.listed_space_inequalities = self._extract_inequalities()
        return self.listed_space_inequalities

    def __str__(self) -> str:
        if self.listed_space_inequalities is None:
            return f"{self.inequalities}"
        return f"{', '.join([str(ineq) for ineq in self.listed_space_inequalities])}"


