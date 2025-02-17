from dataclasses import dataclass

from .constraint import ConstraintImplication, ConstraintAggregationType, SubConstraint
from .constraintI import Constraint
from .invariant.template import InvariantTemplate
from .template import LTLCertificateDecomposedTemplates
from ..polynomial.inequality import EquationConditionType, Inequality
from ..space import SystemSpace


@dataclass
class NonNegativityConstraint(Constraint):
    """
    forall s ∈ R → V(s,q) ≥ 0
    """
    template_manager: LTLCertificateDecomposedTemplates
    invariant: InvariantTemplate
    system_space: SystemSpace

    __slots__ = ["template_manager", "system_space", "invariant"]

    def extract(self) -> list[ConstraintImplication]:
        constraints = []
        self._extract_buchi(constraints=constraints)
        return constraints

    def _extract_buchi(self, constraints):
        for q_id in self.template_manager.buchi_template.sub_templates.keys():
            constraints.append(
                ConstraintImplication(
                    variables=self.template_manager.variable_generators,
                    lhs=SubConstraint(
                        expr_1=self.system_space.space_inequalities,
                        expr_2=self.invariant.get_lhs_invariant(q_id),
                        aggregation_type=ConstraintAggregationType.CONJUNCTION
                    ),
                    rhs=SubConstraint(
                        expr_1=Inequality(
                            left_equation=self.template_manager.buchi_template.sub_templates[q_id],
                            inequality_type=EquationConditionType.GREATER_THAN_OR_EQUAL,
                            right_equation=self.template_manager.variables.zero_eq
                        ),
                        aggregation_type=ConstraintAggregationType.CONJUNCTION
                    )
                )
            )
