from dataclasses import dataclass
from typing import List, Dict

from ..constraint import ConstraintInequality, ConstraintAggregationType, SubConstraint, GuardedInequality
from ..constraintI import Constraint
from .template import InvariantTemplate
from ..utils import _replace_keys_with_values
from ...action import SystemDecomposedControlPolicy, SystemControlPolicy, PolicyType
from ...automata.graph import Automata
from ...dynamics import SystemDynamics, ConditionalDynamics
from ...noise import SystemStochasticNoise
from ...polynomial.equation import Equation
from ...polynomial.inequality import EquationConditionType, Inequality
from ...space import SystemSpace


@dataclass
class InvariantInductiveConstraint(Constraint):
    template: InvariantTemplate
    system_space: SystemSpace
    decomposed_control_policy: SystemDecomposedControlPolicy
    disturbance: SystemStochasticNoise
    system_dynamics: SystemDynamics
    automata: Automata

    __slots__ = ["template", "system_space", "decomposed_control_policy", "disturbance", "system_dynamics", "automata"]

    def extract(self):
        constraints = []
        eq_zero = Equation.extract_equation_from_string("0")
        disturbance_dim = self.disturbance.dimension
        disturbance_var_gens = [f"D{i + 1}" for i in range(disturbance_dim)]
        all_available_variables = self.template.variable_generators + disturbance_var_gens
        acceptance_signatures = [int(_id) for _id in self.automata.accepting_component_ids]
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

        for dynamical in self.system_dynamics.system_transformations:
            self._extract_helper(
                constraints=constraints,
                system_dynamics=dynamical,
                acceptance_signatures=acceptance_signatures,
                eq_zero=eq_zero,
                disturbance_bounds_inequalities=disturbance_bounds_inequalities,
                all_available_variables=all_available_variables
            )
        return constraints

    def _extract_helper(
            self,
            constraints: list[ConstraintInequality],
            system_dynamics: ConditionalDynamics,
            acceptance_signatures: List[int],
            eq_zero,
            disturbance_bounds_inequalities,
            all_available_variables
    ) -> list[ConstraintInequality]:

        for state in self.automata.states:
            current_i = self.template.templates[str(state.state_id)]
            if self.decomposed_control_policy.action_dimension == 0: # TODO: Later fix this using utils for extracting policy
                policies = []
            elif state.is_accepting():
                policies = [self.decomposed_control_policy.get_policy(policy_type=PolicyType.BUCHI, policy_id=_id) for _id in acceptance_signatures]
            else:
                policies = [self.decomposed_control_policy.get_policy(policy_type=PolicyType.REACH)]
            next_state_condition, next_states_under_policies = self._next_sds_state_helper(
                dynamical=system_dynamics,
                policies=policies,
            )
            _next_possible_q_ids = (t.destination for t in state.transitions)
            _next_possible_i_guards = (t.label for t in state.transitions)
            next_possible_invariants = [
                self.template.templates[str(_q_id)]
                for _q_id in _next_possible_q_ids
            ]  # INV(s, q')

            _lhs_next_possible_i_guarded = (
                GuardedInequality(  # if transition (q to q') is possible
                    guard=_guard,  # the label of the transition
                    inequality=Inequality(
                        left_equation=current_i,
                        inequality_type=EquationConditionType.GREATER_THAN_OR_EQUAL,
                        right_equation=eq_zero
                    ),
                    aggregation_type=ConstraintAggregationType.CONJUNCTION,
                    lookup_table=self.automata.lookup_table,
                ) for _guard in _next_possible_i_guards
            )

            lhs_for_each_transition = [
                SubConstraint(
                    expr_1=self.system_space.space_inequalities + disturbance_bounds_inequalities + next_state_condition + [next_possible_i_guarded],
                    aggregation_type=ConstraintAggregationType.CONJUNCTION
                ) for next_possible_i_guarded in _lhs_next_possible_i_guarded
            ]

            for lhs, next_possible_invariant in zip(lhs_for_each_transition, next_possible_invariants):
                self._extract_for_specific_transition_and_policy(
                    constraints=constraints,
                    next_states_under_policies=next_states_under_policies,
                    next_possible_invariant=next_possible_invariant,
                    eq_zero=eq_zero,
                    implication_lhs=lhs,
                    all_available_variables=all_available_variables
                )
        return constraints

    @staticmethod
    def _extract_for_specific_transition_and_policy(
            constraints,
            next_states_under_policies,
            next_possible_invariant,
            eq_zero,
            implication_lhs,
            all_available_variables,
    ):
        _next_possible_updated_invariants = (
            next_possible_invariant(**next_state).replace(" ", "")
            for next_state in next_states_under_policies
        ) # INV(s', q')
        _next_possible_updated_invariants_eq = (
            Equation.extract_equation_from_string(_invariant_str)
            for _invariant_str in _next_possible_updated_invariants
        )

        rhs_inequalities = [
            Inequality(
                left_equation=_invariants_eq,
                inequality_type=EquationConditionType.GREATER_THAN_OR_EQUAL,
                right_equation=eq_zero
            )
            for _invariants_eq in _next_possible_updated_invariants_eq
        ]

        constraints.append(
            ConstraintInequality(
                variables=all_available_variables,
                lhs=implication_lhs,
                rhs=SubConstraint(expr_1=rhs_inequalities,aggregation_type=ConstraintAggregationType.CONJUNCTION)
            )
        )

    @staticmethod
    def _next_sds_state_helper(dynamical: ConditionalDynamics, policies: List[SystemControlPolicy]) -> [List[Inequality], List[Dict[str, str]]]:
        if len(policies) == 0:
            return dynamical.condition, [dynamical({})]
        _actions = [_policy() for _policy in policies]
        return dynamical.condition, [dynamical(_action) for _action in _actions]


def invariant_inductive_inequality_give_transition(
        next_state_under_policy: Dict[str, str],
        zero_equation: Equation,
        invariant_template_manager: InvariantTemplate = None,
        next_state_id: str = None,
        next_invariant: Equation = None,
        noise_bounds: Dict[str, Dict[str, str]] = None
) -> List[Inequality]:

    if next_invariant is None and next_state_id is not None and invariant_template_manager is not None:
        next_invariant = invariant_template_manager.templates[next_state_id] # INV(s, q')
    elif next_invariant is None or invariant_template_manager is None:
        raise ValueError("Next Invariant is not provided. You should provide `next_invariant` or `next_state + template_manager`")

    next_invariant_state_str = next_invariant(**next_state_under_policy).replace(" ", "")  # INV(s', q')
    if noise_bounds is None:
        next_invariant_states = [Equation.extract_equation_from_string(next_invariant_state_str)]
    else:
        next_invariant_states = [
            Equation.extract_equation_from_string(_replace_keys_with_values(next_invariant_state_str, noise_bounds["lower"])),
            Equation.extract_equation_from_string(_replace_keys_with_values(next_invariant_state_str, noise_bounds["upper"]))
        ]

    return [
        Inequality(
            left_equation=next_invariant_state,
            inequality_type=EquationConditionType.GREATER_THAN_OR_EQUAL,
            right_equation=zero_equation
        )
        for next_invariant_state in next_invariant_states
    ]






