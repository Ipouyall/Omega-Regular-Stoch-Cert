from dataclasses import dataclass

from .constraint_inequality import ConstraintInequality, ConstraintAggregationType, SubConstraint
from .constraints import Constraint
from .template import LTLCertificateDecomposedTemplates
from ..polynomial.equation import Equation
from ..polynomial.inequality import EquationConditionType, Inequality
from ..space import SystemSpace


@dataclass
class NonNegativityConstraint(Constraint):
    """
    forall s ∈ R → V(s,q) ≥ 0
    """
    template_manager: LTLCertificateDecomposedTemplates
    system_space: SystemSpace

    __slots__ = ["template_manager", "system_space"]

    def extraxt_reach_and_stay(self) -> list[ConstraintInequality]:
        _ineq = [
            Inequality(
                left_equation=t,
                inequality_type=EquationConditionType.GREATER_THAN_OR_EQUAL,
                right_equation=Equation.extract_equation_from_string("0")
            )
            for t in self.template_manager.reach_and_stay_template.templates.values()
        ]
        _sub = SubConstraint(
            expr_1=_ineq,
            aggregation_type=ConstraintAggregationType.CONJUNCTION
        )

        return [
            ConstraintInequality(
                variables=self.template_manager.variable_generators,
                lhs=SubConstraint(expr_1=self.system_space.space_inequalities, aggregation_type=ConstraintAggregationType.CONJUNCTION),
                rhs=_sub,
            )
        ]

    def extract_buchi(self) -> list[ConstraintInequality]:
        _inequalities = [
            [Inequality(
                left_equation=t,
                inequality_type=EquationConditionType.GREATER_THAN_OR_EQUAL,
                right_equation=Equation.extract_equation_from_string("0")
            ) for t in bt.templates.values()]
            for bt in self.template_manager.buchi_templates
        ]

        return [
            ConstraintInequality(
                variables=self.template_manager.variable_generators,
                lhs=SubConstraint(expr_1=self.system_space.space_inequalities, aggregation_type=ConstraintAggregationType.CONJUNCTION),
                rhs=SubConstraint(expr_1=_ineq, aggregation_type=ConstraintAggregationType.CONJUNCTION),
            )
            for _ineq in _inequalities
        ]

    def extract(self) -> list[ConstraintInequality]:
        return self.extraxt_reach_and_stay() + self.extract_buchi()