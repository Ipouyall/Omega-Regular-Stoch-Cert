from dataclasses import dataclass

from .constraint import ConstraintConstant, SubConstraint
from .constraintI import Constraint
from .template import LTLCertificateDecomposedTemplates
from ..polynomial.inequality import EquationConditionType, Inequality


@dataclass
class TemplateVariablesConstraint(Constraint):
    template_manager: LTLCertificateDecomposedTemplates

    def extract(self) -> list[ConstraintConstant]:
        constraints = []
        self._extract_for_epsilon_safe(constraints=constraints)
        self._extract_for_epsilon_buchi(constraints=constraints)
        self._extract_for_eta_safe_upper(constraints=constraints)
        self._extract_for_delta_buchi(constraints=constraints)
        self._extract_for_eta_epsilon(constraints=constraints)
        return constraints

    def _extract_for_epsilon_safe(self, constraints: list[ConstraintConstant]):
        _inequality = Inequality(
            left_equation=self.template_manager.variables.epsilon_safe_eq,
            inequality_type=EquationConditionType.GREATER_THAN_OR_EQUAL,
            right_equation=self.template_manager.variables.almost_zero_eq
        )
        constraints.append(
            ConstraintConstant(
                sub_constraints=SubConstraint(expr_1=_inequality)
            )
        )

    def _extract_for_epsilon_buchi(self, constraints: list[ConstraintConstant]):
        _inequality = Inequality(
            left_equation=self.template_manager.variables.epsilon_buchi_eq,
            inequality_type=EquationConditionType.GREATER_THAN_OR_EQUAL,
            right_equation=self.template_manager.variables.almost_zero_eq
        )
        constraints.append(
            ConstraintConstant(
                sub_constraints=SubConstraint(expr_1=_inequality)
            )
        )

    def _extract_for_eta_safe_upper(self, constraints: list[ConstraintConstant]):
        _inequality = Inequality(
            left_equation=self.template_manager.variables.eta_safe_eq,
            inequality_type=EquationConditionType.LESS_THAN_OR_EQUAL,
            right_equation=self.template_manager.variables.zero_eq
        )
        constraints.append(
            ConstraintConstant(
                sub_constraints=SubConstraint(expr_1=_inequality)
            )
        )

    def _extract_for_delta_buchi(self, constraints: list[ConstraintConstant]):
        _inequality = Inequality(
            left_equation=self.template_manager.variables.delta_buchi_eq,
            inequality_type=EquationConditionType.GREATER_THAN_OR_EQUAL,
            right_equation=self.template_manager.variables.almost_zero_eq
        )
        constraints.append(
            ConstraintConstant(
                sub_constraints=SubConstraint(expr_1=_inequality)
            )
        )

    def _extract_for_eta_epsilon(self, constraints: list[ConstraintConstant]):
        _inequality = Inequality(
            left_equation=self.template_manager.variables.eta_epsilon_eq,
            inequality_type=EquationConditionType.LESS_THAN_OR_EQUAL,
            right_equation=self.template_manager.variables.eta_epsilon_upper_bound_eq
        )
        constraints.append(
            ConstraintConstant(
                sub_constraints=SubConstraint(expr_1=_inequality)
            )
        )