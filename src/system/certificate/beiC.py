from dataclasses import dataclass

from .constraint import ConstraintImplication, ConstraintAggregationType, SubConstraint, GuardedInequality
from .constraintI import Constraint
from .safety_condition import SafetyConditionHandler
from .utils import _replace_keys_with_values, get_policy_action_given_current_abstract_state
from .invariant.template import InvariantTemplate
from .template import LTLCertificateDecomposedTemplates
from ..action import SystemDecomposedControlPolicy
from ..automata.graph import Automata
from ..automata.sub_graph import AutomataState
from ..dynamics import SystemDynamics, ConditionalDynamics
from ..noise import SystemStochasticNoise
from ..polynomial.equation import Equation
from ..polynomial.inequality import EquationConditionType, Inequality
from ..space import SystemSpace


@dataclass
class BoundedExpectedIncreaseConstraint(Constraint):
    template_manager: LTLCertificateDecomposedTemplates
    invariant: InvariantTemplate
    system_space: SystemSpace
    decomposed_control_policy: SystemDecomposedControlPolicy
    disturbance: SystemStochasticNoise
    system_dynamics: SystemDynamics
    automata: Automata
    safety_condition_handler: SafetyConditionHandler

    __slots__ = [
        "template_manager", "system_space", "invariant", "decomposed_control_policy",
        "disturbance", "automata", "system_dynamics", "safety_condition_handler"
    ]

    def extract(self) -> list[ConstraintImplication]:
        constraints = []
        for dynamics in self.system_dynamics.system_transformations:
            self._extract_bei_given_dynamics(constraints=constraints, system_dynamics=dynamics)
        return constraints

    def _extract_bei_given_dynamics(self, constraints: list[ConstraintImplication], system_dynamics: ConditionalDynamics) -> list[ConstraintImplication]:
        for state in self.automata.states:
            if not state.is_in_accepting_signature(acc_sig=None):
                continue
            self._extract_bei_given_state_and_dynamics(
                constraints=constraints,
                current_state=state,
                system_dynamics=system_dynamics
            )

    def _extract_bei_given_state_and_dynamics(self, constraints: list[ConstraintImplication], current_state: AutomataState, system_dynamics: ConditionalDynamics):
        safety_constraints = self.safety_condition_handler.get_safety_condition(
            current_state=current_state,
            system_dynamics=system_dynamics
        )
        assert len(safety_constraints) == len(current_state.transitions), f"Safety constraints and Current_state.transitions should have the same length. Got {len(safety_constraints)} != {len(current_state.transitions)} for q={current_state.state_id}"

        for tr, safety_constraint in zip(current_state.transitions, safety_constraints):
            _lhs_inequalities = [
                Inequality(
                    left_equation=self.template_manager.safe_template.sub_templates[str(current_state.state_id)],
                    inequality_type=EquationConditionType.LESS_THAN_OR_EQUAL,
                    right_equation=self.template_manager.variables.zero_eq,
                ),
                self.invariant.get_lhs_invariant(str(current_state.state_id)),
            ]
            _lhs_guarded = GuardedInequality(
                guard=tr.label,
                inequality=_lhs_inequalities,
                aggregation_type=ConstraintAggregationType.CONJUNCTION,
                lookup_table=self.automata.lookup_table,
            )  # [V_{safety}(s, q) <= 0] and [INV(s,q)] and [X|=a]
            lhs = SubConstraint(
                expr_1=self.system_space.space_inequalities + system_dynamics.condition,
                expr_2=_lhs_guarded,
                aggregation_type=ConstraintAggregationType.CONJUNCTION,
            )

            control_action = get_policy_action_given_current_abstract_state(
                current_state=current_state,
                decomposed_control_policy=self.decomposed_control_policy
            )
            next_state_under_policy = system_dynamics(control_action)  # Dict: {state_id: StringEquation}
            current_v_buchi = self.template_manager.buchi_template.sub_templates[str(current_state.state_id)]

            _next_possible_v_buchi = self.template_manager.buchi_template.sub_templates[str(tr.destination)] # V_{buchi}(s, q')

            _next_possible_v_buchi_str = _next_possible_v_buchi(**next_state_under_policy).replace(" ", "") # STRING: V_{buchi}(s', q')

            disturbance_expectations = self.disturbance.get_expectations()
            _expected_next_possible_v_buchi_str = _replace_keys_with_values(_next_possible_v_buchi_str, disturbance_expectations) # STRING: E[V_{buchi}(s', q')]

            _expected_next_possible_v_buchi = Equation.extract_equation_from_string(_expected_next_possible_v_buchi_str) # E[V_{buchi}(s', q')]

            _current_v_buchies_add_delta = current_v_buchi.add(self.template_manager.variables.delta_buchi_eq)  # V_{Buchi}(s, q) + \delta_{Buchi}
            bounded_expected_increase_inequalities = Inequality(
                left_equation=_expected_next_possible_v_buchi,
                inequality_type=EquationConditionType.LESS_THAN_OR_EQUAL,
                right_equation=_current_v_buchies_add_delta,
            ) # \delta_{Buchi} + E[V_{buchi}(s', q')] - V_{Buchi}(s, q) >= 0


            rhs = SubConstraint(
                expr_1=safety_constraint,
                expr_2=bounded_expected_increase_inequalities,
                aggregation_type=ConstraintAggregationType.CONJUNCTION,
            )
            constraints.append(
                ConstraintImplication(
                    variables=self.template_manager.variable_generators,
                    lhs=lhs,
                    rhs=rhs,
                )
            )
