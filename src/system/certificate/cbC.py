from dataclasses import dataclass

from .constraint import ConstraintImplication, ConstraintAggregationType, SubConstraint
from .constraintI import Constraint
from .template import LTLCertificateDecomposedTemplates
from ..action import SystemDecomposedControlPolicy
from ..polynomial.equation import Equation
from ..polynomial.inequality import EquationConditionType, Inequality
from ..space import SystemSpace


@dataclass
class ControllerBounds(Constraint):
    template_manager: LTLCertificateDecomposedTemplates
    system_space: SystemSpace
    decomposed_control_policy: SystemDecomposedControlPolicy

    __slots__ = ["decomposed_control_policy", "system_space", "template_manager"]

    def extract(self) -> list[ConstraintImplication]:
        constraints = []
        limits = self.decomposed_control_policy.get_limits()
        min_limit = limits["min"]
        if min_limit is not None:
            min_limit = Equation.extract_equation_from_string(str(min_limit))
        max_limit = limits["max"]
        if max_limit is not None:
            max_limit = Equation.extract_equation_from_string(str(max_limit))

        for policy in self.decomposed_control_policy.policies:
            for tr in policy.transitions:
                _ineqs = self._extract_boundaries_for_policy_caused_transition(tr, min_limit, max_limit)
                if not _ineqs:
                    continue
                constraints.append(
                    ConstraintImplication(
                        variables=self.template_manager.variable_generators,
                        lhs=SubConstraint(expr_1=self.system_space.space_inequalities, aggregation_type=ConstraintAggregationType.CONJUNCTION),
                        rhs=SubConstraint(expr_1=_ineqs, aggregation_type=ConstraintAggregationType.CONJUNCTION),
                    )
                )
        return constraints

    @staticmethod
    def _extract_boundaries_for_policy_caused_transition(transition: Equation, minimum: Equation, maximum: Equation):
        _ineqs = []
        if minimum is not None:
            _ineqs.append(
                Inequality(
                    left_equation=transition,
                    inequality_type=EquationConditionType.GREATER_THAN_OR_EQUAL,
                    right_equation=minimum
                )
            )
        if maximum is not None:
            _ineqs.append(
                Inequality(
                    left_equation=transition,
                    inequality_type=EquationConditionType.LESS_THAN_OR_EQUAL,
                    right_equation=maximum
                )
            )
        return _ineqs
