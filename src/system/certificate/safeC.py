from dataclasses import dataclass

from .constraint import ConstraintImplication, ConstraintAggregationType, SubConstraint
from .constraintI import Constraint
from .invariant.template import InvariantTemplate
from .template import LTLCertificateDecomposedTemplates
from ..automata.graph import Automata
from ..polynomial.inequality import EquationConditionType, Inequality
from ..space import SystemSpace


@dataclass
class SafetyConstraint(Constraint):
    template_manager: LTLCertificateDecomposedTemplates
    invariant: InvariantTemplate
    system_space: SystemSpace
    automata: Automata

    def extract(self) -> list[ConstraintImplication]:
        constraints = []
        self._extract_safety_on_rejecting_set(constraints=constraints)
        return constraints

    def _extract_safety_on_rejecting_set(self, constraints):
        """
        forall X in SystemSpace and Q in Q_{reject} => V{safe}(X, Q) >= 0
        """

        for rej_state_id in self.automata.rejecting_states_ids:
            rhs_inequality = Inequality(
                left_equation=self.template_manager.safe_template.sub_templates[str(rej_state_id)],
                inequality_type=EquationConditionType.GREATER_THAN_OR_EQUAL,
                right_equation=self.template_manager.variables.zero_eq
            )

            constraints.append(
                ConstraintImplication(
                    variables=self.template_manager.variable_generators,
                    lhs=SubConstraint(
                        expr_1=self.system_space.space_inequalities,
                        expr_2=self.invariant.get_lhs_invariant(str(rej_state_id)),
                        aggregation_type=ConstraintAggregationType.CONJUNCTION
                    ),
                    rhs=SubConstraint(expr_1=[rhs_inequality], aggregation_type=ConstraintAggregationType.CONJUNCTION)
                )
            )

