from dataclasses import dataclass

from .constraint import ConstraintImplication, ConstraintAggregationType, SubConstraint
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
            rhs = self._extract_bei_rhs_given_state_and_dynamics(current_state=state, system_dynamics=system_dynamics)
            left_land_side = Inequality(
                left_equation=self.template_manager.safe_template.sub_templates[str(state.state_id)],
                inequality_type=EquationConditionType.LESS_THAN_OR_EQUAL,
                right_equation=self.template_manager.variables.zero_eq,
            )
            constraints.append(
                ConstraintImplication(
                    variables=self.template_manager.variable_generators,
                    lhs=SubConstraint(
                        expr_1=self.system_space.space_inequalities + system_dynamics.condition,
                        expr_2=[left_land_side, self.invariant.get_lhs_invariant(str(state.state_id))],
                        aggregation_type=ConstraintAggregationType.CONJUNCTION
                    ),
                    rhs=rhs,
                )
            )

    def _extract_bei_rhs_given_state_and_dynamics(self, current_state: AutomataState, system_dynamics: ConditionalDynamics) -> SubConstraint:
        safety_constraints = self.safety_condition_handler.get_safety_condition(
            current_state=current_state,
            system_dynamics=system_dynamics
        )
        control_action = get_policy_action_given_current_abstract_state(
            current_state=current_state,
            decomposed_control_policy=self.decomposed_control_policy
        )
        next_state_under_policy = system_dynamics(control_action)  # Dict: {state_id: StringEquation}
        current_v_buchi = self.template_manager.buchi_template.sub_templates[str(current_state.state_id)]

        _next_possible_v_buchies = (
            self.template_manager.buchi_template.sub_templates[str(tr.destination)]
            for tr in current_state.transitions
        )  # V_{buchi}(s, q')
        _next_possible_v_buchies_str = [
            _v(**next_state_under_policy).replace(" ", "")
            for _v in _next_possible_v_buchies
        ]  # STRING: V_{buchi}(s', q')

        disturbance_expectations = self.disturbance.get_expectations()
        _expected_next_possible_v_buchies_str = (
            _replace_keys_with_values(_v, disturbance_expectations)
            for _v in _next_possible_v_buchies_str
        )  # STRING: E[V_{buchi}(s', q')]
        _expected_next_possible_v_buchies = (
            Equation.extract_equation_from_string(_v)
            for _v in _expected_next_possible_v_buchies_str
        )  # E[V_{buchi}(s', q')]

        _current_v_buchies_add_delta = current_v_buchi.add(self.template_manager.variables.delta_buchi_eq)  # V_{Buchi}(s, q) + \delta_{Buchi}
        bounded_expected_increase_inequalities = [
            Inequality(
                left_equation=_exp,
                inequality_type=EquationConditionType.LESS_THAN_OR_EQUAL,
                right_equation=_current_v_buchies_add_delta,
            )
            for _exp in _expected_next_possible_v_buchies
        ]  # \delta_{Buchi} + E[V_{buchi}(s', q')] - V_{Buchi}(s, q) >= 0

        assert len(safety_constraints) == len(bounded_expected_increase_inequalities), "Safety constraints and bounded expected increase inequalities should have the same length."

        rhs_term_wise = [
            SubConstraint(
                # expr_1=_safe,
                expr_2=_bei,
                aggregation_type=ConstraintAggregationType.CONJUNCTION,
            )
            for _safe, _bei in zip(safety_constraints, bounded_expected_increase_inequalities)
        ]
        return SubConstraint(
            expr_1=rhs_term_wise,
            aggregation_type=ConstraintAggregationType.DISJUNCTION,
        )
