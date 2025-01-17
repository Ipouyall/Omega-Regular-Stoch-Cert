from dataclasses import dataclass

from src.system.certificate.constraint import ConstraintInequality, ConstraintAggregationType, GuardedInequality, SubConstraint
from src.system.certificate.constraintI import Constraint
from src.system.certificate.utils import _replace_keys_with_values
from src.system.certificate.invariant.template import InvariantTemplate
from src.system.certificate.template import LTLCertificateDecomposedTemplates
from src.system.action import SystemDecomposedControlPolicy, PolicyType
from src.system.automata.graph import Automata
from src.system.dynamics import SystemDynamics, ConditionalDynamics
from src.system.noise import SystemStochasticNoise
from src.system.polynomial.equation import Equation
from src.system.polynomial.inequality import EquationConditionType, Inequality
from src.system.space import SystemSpace
#
# @dataclass
# class NonStrictExpectedDecrease(Constraint):
#     template_manager: LTLCertificateDecomposedTemplates
#     invariant: InvariantTemplate
#     system_space: SystemSpace
#     decomposed_control_policy: SystemDecomposedControlPolicy
#     disturbance: SystemStochasticNoise
#     system_dynamics: SystemDynamics
#     automata: Automata
#     epsilon: float
#     probability_threshold: float
#
#     __slots__ = [
#         "template_manager", "system_space", "invariant", "decomposed_control_policy",
#         "disturbance", "system_dynamics", "automata", "epsilon", "probability_threshold"
#     ]
#
#     def extract(self) -> list[ConstraintInequality]:
#         constraints = []
#         self.extraxt_reach_and_stay(constraints=constraints)
#         self.extract_buchi(constraints=constraints)
#         return constraints
#
#     def extraxt_reach_and_stay(self, constraints):
#         _p = Equation.extract_equation_from_string(f"1/(1-{self.probability_threshold})")
#         _eq_zero = Equation.extract_equation_from_string("0")
#
#         for dynamical in self.system_dynamics.system_transformations:
#             self.extraxt_reach_and_stay_helper(
#                 constraints=constraints,
#                 _p=_p,
#                 _eq_zero=_eq_zero,
#                 system_dynamics=dynamical
#             )
#
#
#     def extraxt_reach_and_stay_helper(
#             self,
#             constraints,
#             _p: Equation,
#             _eq_zero: Equation,
#             system_dynamics: ConditionalDynamics,
#     )-> list[ConstraintInequality]:
#         """
#         forall S and q ∈ Q_{acc}, [1/(1-p) - V^{reach-and-stay}(s,q) >= 0] → [V^{reach-and-stay}(s,q) − E[V^{reach-and-stay}(s',q')]≥ 0]
#         """
#         #  S' under π_accept
#         _s_ra_control_policy_accept = self.decomposed_control_policy.get_policy(PolicyType.ACCEPTANCE)
#         _s_control_action_accept = _s_ra_control_policy_accept()
#         _s_next_states_under_accept = system_dynamics(_s_control_action_accept)  # Dict: {state_id: StringEquation}
#
#         for _q_id in range(self.template_manager.abstraction_dimension):
#             q = self.automata.get_state(_q_id)
#             # q ∈ Q_{accept}
#             if not q.is_accepting():
#                 continue
#
#             # V(s,q) <= 1/(1-p) == 1/(1-p) - V(s,q) >= 0
#             current_v = self.template_manager.reach_template.decomposed_sub_templates[str(_q_id)]
#             _left_land_side = Inequality(
#                 left_equation=_p.sub(current_v),
#                 inequality_type=EquationConditionType.GREATER_THAN_OR_EQUAL,
#                 right_equation=_eq_zero
#             )
#
#             # V(s, q')
#             next_possible_q_ids = (t.destination for t in q.transitions)
#             next_possible_v_guards = (t.label for t in q.transitions)
#             next_possible_v = (
#                 self.template_manager.reach_template.decomposed_sub_templates[str(_q_id)]
#                 for _q_id in next_possible_q_ids
#             )
#
#             # V(s', q')
#             possible_next_vs = [
#                 _v(**_s_next_states_under_accept).replace(" ", "")
#                 for _v in next_possible_v
#             ]
#
#             # E[V(s',q')]
#             disturbance_expectations = self.disturbance.get_expectations()
#             expected_possible_next_vs = (
#                 _replace_keys_with_values(_v, disturbance_expectations)
#                 for _v in possible_next_vs
#             )
#             expected_next_v_eq = [
#                 Equation.extract_equation_from_string(_v)
#                 for _v in expected_possible_next_vs
#             ]
#
#             # V(s,q) − E[V(s',q')]
#             _t_right_hand_sides = (
#                 current_v.sub(_expected_v)
#                 for _expected_v in expected_next_v_eq
#             )
#             _right_hand_sides = [
#                 GuardedInequality(  # if transition (q to q') is possible, then:  V(s,q) − E[V(s',q')] ≥ 0
#                     guard=_guard,  # the label of the transition
#                     inequality=Inequality(  # V(s,q) − E[V(s',q')] ≥ 0
#                         left_equation=_lhs,
#                         inequality_type=EquationConditionType.GREATER_THAN_OR_EQUAL,
#                         right_equation=_eq_zero
#                     ),
#                     aggregation_type=ConstraintAggregationType.CONJUNCTION,
#                     lookup_table=self.automata.lookup_table,
#                 )
#                 for _lhs, _guard in zip(_t_right_hand_sides, next_possible_v_guards)
#             ]
#             constraints.append(
#                 ConstraintInequality(  # [1/(1-p) - V(s,q) >= 0] → [V(s,q) − E[V(s',q')] ≥ 0]
#                     variables=self.template_manager.variable_generators,
#                     lhs=SubConstraint(
#                         expr_2=self.system_space.space_inequalities+system_dynamics.condition,
#                         expr_1=[_left_land_side, self.invariant.get_lhs_invariant(str(_q_id))],
#                         aggregation_type=ConstraintAggregationType.CONJUNCTION
#                     ),
#                     rhs=SubConstraint(
#                         expr_1=_right_hand_sides,
#                         aggregation_type=ConstraintAggregationType.DISJUNCTION
#                     ),
#                 )
#             )
#         return constraints
#
#     def extract_buchi(self, constraints):
#         _p = Equation.extract_equation_from_string(f"1/(1-{self.probability_threshold})")
#         _eq_zero = Equation.extract_equation_from_string("0")
#
#         for dynamical in self.system_dynamics.system_transformations:
#             self.extract_buchi_helper(
#                 constraints=constraints,
#                 _p=_p,
#                 _eq_zero=_eq_zero,
#                 system_dynamics=dynamical
#             )
#
#
#     def extract_buchi_helper(
#             self,
#             constraints,
#             _p: Equation,
#             _eq_zero: Equation,
#             system_dynamics: ConditionalDynamics,
#     ) -> list[ConstraintInequality]:
#         """
#         Non-strict expected decrease in V^{reach-and-stay} under π_{i} within F_{i} for q ∈ Q_{accept} ∩ F_{i}:
#         [1/(1-p) - V^{reach-and-stay}(s,q) >= 0] → [V^{reach-and-stay}(s,q) − E[V^{reach-and-stay}(s',q')] ≥ 0]
#         """
#         buchi_counts = self.decomposed_control_policy.get_length()[PolicyType.BUCHI]
#         for _buchi_id in range(buchi_counts):  # for each buchi i
#             _buchi_control_policy = self.decomposed_control_policy.get_policy(policy_type=PolicyType.BUCHI, policy_id=_buchi_id)
#             _s_control_action_buchi = _buchi_control_policy()
#             _s_next_states_under_buchi = system_dynamics(_s_control_action_buchi)
#
#             for _q_id in range(self.template_manager.abstraction_dimension):
#                 q = self.automata.get_state(_q_id)
#                 # q ∈ Q_{accept} ∩ F_{i}
#                 if not (q.is_accepting() and q.is_in_accepting_signature(_buchi_id)):
#                     continue
#                 #  V^{reach-and-stay}(s,q) <= 1/(1-p) == 1/(1-p) - V^{reach-and-stay}(s,q) >= 0
#                 current_v_reach_and_stay = self.template_manager.reach_template.decomposed_sub_templates[str(_q_id)]
#                 _left_land_side = Inequality(
#                     left_equation=_p.sub(current_v_reach_and_stay),
#                     inequality_type=EquationConditionType.GREATER_THAN_OR_EQUAL,
#                     right_equation=_eq_zero
#                 )
#
#                 #  V^{reach-and-stay}(s, q')
#                 next_possible_q_ids = (t.destination for t in q.transitions)
#                 next_possible_v_guards = (t.label for t in q.transitions)
#                 next_possible_v_reach_and_stay = (
#                     self.template_manager.reach_template.decomposed_sub_templates[str(_q_id)]
#                     for _q_id in next_possible_q_ids
#                 )
#                 #  V^{reach-and-stay}(s', q')
#                 possible_next_vs_reach_and_stay = (
#                     _v(**_s_next_states_under_buchi).replace(" ", "")
#                     for _v in next_possible_v_reach_and_stay
#                 )
#                 # E[V^{reach-and-stay}(s',q')]
#                 disturbance_expectations = self.disturbance.get_expectations()
#                 expected_possible_next_vs_reach_and_stay = (
#                     _replace_keys_with_values(_v, disturbance_expectations)
#                     for _v in possible_next_vs_reach_and_stay
#                 )
#                 expected_next_v_eq_reach_and_stay = (
#                     Equation.extract_equation_from_string(_v)
#                     for _v in expected_possible_next_vs_reach_and_stay
#                 )
#                 # V^{reach-and-stay}(s,q) − E[V^{reach-and-stay}(s',q')
#                 _t_right_hand_sides_reach_and_stay = (
#                     current_v_reach_and_stay.sub(_expected_v)
#                     for _expected_v in expected_next_v_eq_reach_and_stay
#                 )
#                 # V^{reach-and-stay}(s,q) − E[V^{reach-and-stay}(s',q')] ≥ 0
#                 _rhs_reach_and_stay = (
#                     Inequality(
#                         left_equation=_lhs,
#                         inequality_type=EquationConditionType.GREATER_THAN_OR_EQUAL,
#                         right_equation=_eq_zero
#                     )
#                     for _lhs in _t_right_hand_sides_reach_and_stay
#                 )
#
#                 # if transition (q to q') is possible, then:  V^{reach-and-stay}(s,q) − E[V^{reach-and-stay}(s',q')] ≥ 0
#                 _rhs = [
#                     GuardedInequality(
#                         guard=_guard,
#                         inequality=_ineq,
#                         lookup_table=self.automata.lookup_table,
#                     )
#                     for _ineq, _guard in zip(_rhs_reach_and_stay, next_possible_v_guards)
#                 ]
#
#                 constraints.append(
#                     ConstraintInequality(
#                         variables=self.template_manager.variable_generators,
#                         lhs=SubConstraint(
#                             expr_2=self.system_space.space_inequalities+system_dynamics.condition,
#                             expr_1=[_left_land_side, self.invariant.get_lhs_invariant(str(_q_id))],
#                             aggregation_type=ConstraintAggregationType.CONJUNCTION),
#                         rhs=SubConstraint(expr_1=_rhs, aggregation_type=ConstraintAggregationType.DISJUNCTION),
#                     )
#                 )
#         return constraints
