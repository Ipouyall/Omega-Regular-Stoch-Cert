from dataclasses import dataclass

from src.system.certificate.constraint import ConstraintImplication, ConstraintAggregationType, SubConstraint
from src.system.certificate.constraintI import Constraint
from src.system.certificate.invariant.template import InvariantTemplate
from src.system.certificate.template import LTLCertificateDecomposedTemplates
from src.system.polynomial.equation import Equation
from src.system.polynomial.inequality import EquationConditionType, Inequality
from src.system.space import SystemSpace


# @dataclass
# class NonNegativityConstraint(Constraint):
#     """
#     forall s ∈ R → V(s,q) ≥ 0
#     """
#     template_manager: LTLCertificateDecomposedTemplates
#     invariant: InvariantTemplate
#     system_space: SystemSpace
#
#     __slots__ = ["template_manager", "system_space", "invariant"]
#
#     def _extraxt_reach_and_stay_inequalities(self, q: str) -> list[Inequality]:
#         return [
#             Inequality(
#                 left_equation=self.template_manager.reach_template.decomposed_sub_templates[q],
#                 inequality_type=EquationConditionType.GREATER_THAN_OR_EQUAL,
#                 right_equation=Equation.extract_equation_from_string("0")
#             )
#         ]
#
#     def _extract_buchi_inequalities(self, q: str) -> list[Inequality]:
#         return [
#             Inequality(
#                 left_equation=self.template_manager.buchi_template.decomposed_sub_templates[q],
#                 inequality_type=EquationConditionType.GREATER_THAN_OR_EQUAL,
#                 right_equation=Equation.extract_equation_from_string("0")
#             )
#         ]
#
#     def extract(self) -> list[ConstraintInequality]:
#         constraints = []
#         for q in self.template_manager.reach_template.decomposed_sub_templates.keys():
#             constraints.append(
#                 ConstraintInequality(
#                     variables=self.template_manager.variable_generators,
#                     lhs=SubConstraint(
#                         expr_1=self.system_space.space_inequalities,
#                         expr_2=self.invariant.get_lhs_invariant(q),
#                         aggregation_type=ConstraintAggregationType.CONJUNCTION
#                     ),
#                     rhs=SubConstraint(
#                         expr_1=self._extraxt_reach_and_stay_inequalities(q) + self._extract_buchi_inequalities(q),
#                         aggregation_type=ConstraintAggregationType.CONJUNCTION
#                     )
#                 )
#             )
#         return constraints










