from dataclasses import dataclass

from .constraint import ConstraintImplication, ConstraintAggregationType, SubConstraint
from .constraintI import Constraint
from .template import LTLCertificateDecomposedTemplates
from ..automata.graph import Automata
from ..polynomial.inequality import EquationConditionType, Inequality
from ..space import SystemSpace


@dataclass
class InitialSpaceConstraint(Constraint):
    template_manager: LTLCertificateDecomposedTemplates
    system_space: SystemSpace
    initial_space: SystemSpace
    automata: Automata

    def extract(self) -> list[ConstraintImplication]:
        constraints = []
        self.extraxt_safe(constraints=constraints)
        return constraints

    __slots__ = ["template_manager", "system_space", "automata"]

    def extraxt_safe(self, constraints):
        """
        \forall X \in \Init -> V_{safe}(X, q_{init}) <= -\eta^S
        """
        _initial_state = self.automata.start_state_id
        _ineq = Inequality(
            left_equation=self.template_manager.safe_template.sub_templates[_initial_state],
            inequality_type=EquationConditionType.LESS_THAN_OR_EQUAL,
            right_equation=self.template_manager.variables.eta_safe_eq
        )

        constraints.append(
            ConstraintImplication(
                variables=self.template_manager.variable_generators,
                lhs=SubConstraint(
                    expr_1=self.system_space.space_inequalities + self.initial_space.space_inequalities,
                    aggregation_type=ConstraintAggregationType.CONJUNCTION
                ),
                rhs=SubConstraint(expr_1=_ineq, aggregation_type=ConstraintAggregationType.CONJUNCTION)
            )
        )

        return constraints
