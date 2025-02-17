from dataclasses import dataclass

from ..constraint import ConstraintImplication, ConstraintAggregationType, SubConstraint
from ..constraintI import Constraint
from .template import InvariantTemplate
from ...automata.graph import Automata
from ...polynomial.equation import Equation
from ...polynomial.inequality import EquationConditionType, Inequality
from ...space import SystemSpace


@dataclass
class InvariantInitialConstraint(Constraint):
    template: InvariantTemplate
    system_space: SystemSpace
    initial_space: SystemSpace
    automata: Automata

    __slots__ = ["template", "system_space", "initial_space", "automata"]

    def extract(self) -> list[ConstraintImplication]:
        _eq_zero = Equation.extract_equation_from_string("0")
        _initial_state = self.automata.start_state_id
        _ineq = Inequality(
            left_equation=self.template.templates[_initial_state],
            inequality_type=EquationConditionType.GREATER_THAN_OR_EQUAL,
            right_equation=_eq_zero
        )
        template_rhs = SubConstraint(
            expr_1=_ineq,
            aggregation_type=ConstraintAggregationType.CONJUNCTION
        )
        return [
            ConstraintImplication(
                variables=self.template.variable_generators,
                lhs=SubConstraint(
                    expr_1=self.system_space.space_inequalities + self.initial_space.space_inequalities,
                    aggregation_type=ConstraintAggregationType.CONJUNCTION),
                rhs=template_rhs,
            )
        ]


