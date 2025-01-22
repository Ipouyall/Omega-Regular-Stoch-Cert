from dataclasses import dataclass

from .constraint import ConstraintInequality, ConstraintAggregationType, SubConstraint, GuardedInequality
from .constraintI import Constraint
from .safety_condition import SafetyConditionHandler
from .invariant.template import InvariantTemplate
from .template import LTLCertificateDecomposedTemplates
from ..action import SystemDecomposedControlPolicy, PolicyType, SystemControlPolicy
from ..automata.graph import Automata
from ..dynamics import SystemDynamics, ConditionalDynamics
from ..noise import SystemStochasticNoise
from ..polynomial.equation import Equation
from ..polynomial.inequality import EquationConditionType, Inequality
from ..space import SystemSpace


@dataclass
class BuchiBoundedDifferenceConstraint(Constraint):
    template_manager: LTLCertificateDecomposedTemplates
    invariant: InvariantTemplate
    system_space: SystemSpace
    decomposed_control_policy: SystemDecomposedControlPolicy
    disturbance: SystemStochasticNoise
    system_dynamics: SystemDynamics
    automata: Automata

    __slots__ = [
        "template_manager", "system_space", "invariant", "decomposed_control_policy",
        "disturbance", "automata", "system_dynamics"
    ]

    def extract(self) -> list[ConstraintInequality]:
        constraints = []

        disturbance_var_gens = [f"D{i + 1}" for i in range(self.disturbance.dimension)]
        all_available_variables = self.template_manager.variable_generators + disturbance_var_gens

        disturbance_bounds_inequalities = []
        disturbance_ranges = self.disturbance.get_bounds()
        for sym, ranges in disturbance_ranges.items():
            if "min" in ranges:
                disturbance_bounds_inequalities.append(
                    Inequality(
                        left_equation=Equation.extract_equation_from_string(sym),
                        inequality_type=EquationConditionType.GREATER_THAN_OR_EQUAL,
                        right_equation=Equation.extract_equation_from_string(str(ranges["min"]))
                    )
                )
            if "max" in ranges:
                disturbance_bounds_inequalities.append(
                    Inequality(
                        left_equation=Equation.extract_equation_from_string(sym),
                        inequality_type=EquationConditionType.LESS_THAN_OR_EQUAL,
                        right_equation=Equation.extract_equation_from_string(str(ranges["max"]))
                    )
                )

        for dynamics in self.system_dynamics.system_transformations:
            self._extract_bbd_given_dynamics(
                constraints=constraints,
                system_dynamics=dynamics,
                disturbance_bounds=disturbance_bounds_inequalities,
                all_available_variables=all_available_variables
            )
        return constraints

    def _extract_bbd_given_dynamics(self, constraints: list[ConstraintInequality], system_dynamics: ConditionalDynamics, disturbance_bounds: list[Inequality], all_available_variables):
        for state in self.automata.states:
            current_v_safe = self.template_manager.safe_template.sub_templates[str(state.state_id)]
            if self.decomposed_control_policy.action_dimension == 0: # TODO: Later fix this using utils for extracting policy
                policies = []
            elif state.is_accepting():
                policies = [self.decomposed_control_policy.get_policy(policy_type=PolicyType.BUCHI)]
            else:
                policies = [self.decomposed_control_policy.get_policy(policy_type=PolicyType.REACH)]
            next_state_condition, next_states_under_policies = self._next_sds_state_helper(
                dynamical=system_dynamics,
                policies=policies,
            )
            assert len(next_states_under_policies) == 1, f"Next states under policies should be 1, provided {len(next_states_under_policies)}. Note that this implementation doesn't accept multiple policy"
            next_states_under_policies = next_states_under_policies[0]

            for trans in state.transitions:
                lhs_guards = GuardedInequality(
                    guard=trans.label,  # the label of the transition
                    inequality=[
                        self.invariant.get_lhs_invariant(str(state.state_id)), # Inv(s,q)
                        Inequality(
                            left_equation=current_v_safe,
                            inequality_type=EquationConditionType.LESS_THAN_OR_EQUAL,
                            right_equation=self.template_manager.variables.zero_eq,
                        ),  # V_{safe}(s, q) <= 0
                    ],  # [Inv(s,q)] & [V_{safe}(s, q) <= 0]
                    aggregation_type=ConstraintAggregationType.CONJUNCTION,
                    lookup_table=self.automata.lookup_table,
                ) # [X |= Tr] & [Inv(s,q)] & [V_{safe}(s, q) <= 0]

                lhs = SubConstraint(
                    expr_1=self.system_space.space_inequalities + disturbance_bounds + next_state_condition + [lhs_guards],
                    aggregation_type=ConstraintAggregationType.CONJUNCTION
                )
                rhs = self._extract_bbd_rhs(
                    current_state_id=state.state_id,
                    next_state_id=trans.destination,
                    next_states_under_policies=next_states_under_policies,
                )

                constraint = ConstraintInequality(
                    variables=all_available_variables,
                    lhs=lhs,
                    rhs=rhs,
                )
                constraints.append(constraint)

    def _extract_bbd_rhs(self, current_state_id: int, next_state_id : int, next_states_under_policies: dict[str, str]) -> SubConstraint:
        current_v_buchi = self.template_manager.buchi_template.sub_templates[str(current_state_id)]
        next_v_buchi = self.template_manager.buchi_template.sub_templates[str(next_state_id)]
        beta = self.template_manager.variables.Beta_safe_eq
        delta = self.template_manager.variables.delta_buchi_eq

        current_v_minus_beta = current_v_buchi.sub(beta)

        next_v_buchi_str = next_v_buchi(**next_states_under_policies).replace(" ", "")
        next_v_buchi_eq = Equation.extract_equation_from_string(next_v_buchi_str)
        current_v_minus_beta_minus_next_v = current_v_minus_beta.sub(next_v_buchi_eq) # Vbuchi(x,q) - Vbuchi(f(x,pi(x),w),q') - beta

        _inequalities = [
            Inequality(
                left_equation=current_v_minus_beta_minus_next_v,
                inequality_type=EquationConditionType.GREATER_THAN_OR_EQUAL,
                right_equation=self.template_manager.variables.zero_eq
            ), # Vbuchi(x,q) - Vbuchi(f(x,pi(x),w),q') - beta >= 0
            Inequality(
                left_equation=current_v_minus_beta_minus_next_v,
                inequality_type=EquationConditionType.LESS_THAN_OR_EQUAL,
                right_equation=delta
            ), # Vbuchi(x,q) - Vbuchi(f(x,pi(x),w),q') - beta <= delta
        ] # [Vbuchi(x,q) - Vbuchi(f(x,pi(x),w),q') - beta >= 0] & [Vbuchi(x,q) - Vbuchi(f(x,pi(x),w),q') - beta <= delta]

        return SubConstraint(
            expr_1=_inequalities,
            aggregation_type=ConstraintAggregationType.CONJUNCTION
        )

    @staticmethod
    def _next_sds_state_helper(dynamical: ConditionalDynamics, policies: list[SystemControlPolicy]) -> [
        list[Inequality], list[dict[str, str]]]:
        if len(policies) == 0:
            return dynamical.condition, [dynamical({})]
        _actions = [_policy() for _policy in policies]
        return dynamical.condition, [dynamical(_action) for _action in _actions]

