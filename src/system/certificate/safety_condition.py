from dataclasses import dataclass

from .constraint import ConstraintAggregationType, GuardedInequality, SubConstraint
from .utils import _replace_keys_with_values, get_policy_action_given_current_abstract_state
from .template import LTLCertificateDecomposedTemplates
from ..action import SystemDecomposedControlPolicy
from ..automata.graph import Automata
from ..automata.sub_graph import AutomataState
from ..dynamics import ConditionalDynamics
from ..noise import SystemStochasticNoise
from ..polynomial.equation import Equation
from ..polynomial.inequality import EquationConditionType, Inequality


@dataclass
class SafetyConditionHandler:
    template_manager: LTLCertificateDecomposedTemplates
    decomposed_control_policy: SystemDecomposedControlPolicy
    disturbance: SystemStochasticNoise
    automata: Automata

    def get_safety_condition(self, current_state: AutomataState, system_dynamics: ConditionalDynamics) -> list[SubConstraint]:
        return self._extraxt_safe_condition_helper(
            current_state=current_state,
            system_dynamics=system_dynamics,
        )

    def _extraxt_safe_condition_helper(self, current_state: AutomataState, system_dynamics: ConditionalDynamics) -> list[SubConstraint]:
        control_action = get_policy_action_given_current_abstract_state(
            current_state=current_state,
            decomposed_control_policy=self.decomposed_control_policy,
        )   ### TODO: This part can be passed for optimization
        next_state_under_policy = system_dynamics(control_action)  # Dict: {state_id: StringEquation}   ### TODO: This part can be passed for optimization

        current_v_safety = self.template_manager.safe_template.sub_templates[str(current_state.state_id)]
        _next_possible_v_safeties = (
            self.template_manager.safe_template.sub_templates[str(tr.destination)]
            for tr in current_state.transitions
        ) # V_{safety}(s, q')
        next_possible_v_safeties_str = [
            _v(**next_state_under_policy).replace(" ", "")
            for _v in _next_possible_v_safeties
        ] # STRING: V_{safety}(s', q')
        _next_transitions_label = (
            tr.label
            for tr in current_state.transitions
        )

        disturbance_expectations = self.disturbance.get_expectations()
        _expected_next_possible_v_safeties_str = (
            _replace_keys_with_values(_v, disturbance_expectations)
            for _v in next_possible_v_safeties_str
        ) # STRING: E[V_{safety}(s', q')]
        _expected_next_possible_v_safeties = (
            Equation.extract_equation_from_string(_v)
            for _v in _expected_next_possible_v_safeties_str
        ) # E[V_{safety}(s', q')]
        current_v_sub_safeties_epsilon = current_v_safety.sub(self.template_manager.variables.epsilon_safe_eq) # V_{safety}(s, q) - \epsilon_{Safety}
        _current_v_sub_safeties_epsilon_sub_expected_next_possible_v = (
            current_v_sub_safeties_epsilon.sub(_v)
            for _v in _expected_next_possible_v_safeties
        ) # V_{safety}(s, q) - \epsilon_{Safety} - E[V_{safety}(s', q')]
        _strict_expected_decrease_inequalities = (
            Inequality(
                left_equation=_sed,
                inequality_type=EquationConditionType.GREATER_THAN_OR_EQUAL,
                right_equation=self.template_manager.variables.zero_eq
            )
            for _sed in _current_v_sub_safeties_epsilon_sub_expected_next_possible_v
        ) # V_{safety}(s, q) >= E[V_{safety}(s', q')] + \epsilon_{Safety}
        _guarded_sed = (
            GuardedInequality(
                inequality=_sed,
                guard=_label,
                aggregation_type=ConstraintAggregationType.CONJUNCTION,
                lookup_table=self.automata.lookup_table,
            )
            for _sed, _label in zip(_strict_expected_decrease_inequalities, _next_transitions_label)
        ) #  (X |= a) and (V_{safety}(s, q) >= E[V_{safety}(s', q')] + \epsilon_{safety})

        beta_safety = self.template_manager.variables.Beta_safe_eq

        noise_bounds = self.disturbance.get_bounds()
        lower_bounds = {var: bounds["min"] for var, bounds in noise_bounds.items()}
        upper_bounds = {var: bounds["max"] for var, bounds in noise_bounds.items()}

        _next_possible_v_safeties_bounded = {
            "lower": (_replace_keys_with_values(_v, lower_bounds) for _v in next_possible_v_safeties_str),
            "upper": (_replace_keys_with_values(_v, upper_bounds) for _v in next_possible_v_safeties_str),
        } # STRING: V_{safety}(s', q') with bounds
        _next_possible_v_safeties_eq = {
            "lower": (Equation.extract_equation_from_string(_v) for _v in _next_possible_v_safeties_bounded["lower"]),
            "upper": (Equation.extract_equation_from_string(_v) for _v in _next_possible_v_safeties_bounded["upper"]),
        } # V_{safety}(s', q')
        _beta_safety_add_next_possible_v = {
            "lower": (beta_safety.add(_v) for _v in _next_possible_v_safeties_eq["lower"]),
            "upper": (beta_safety.add(_v) for _v in _next_possible_v_safeties_eq["upper"]),
        } # Beta_{safety} + V_{safety}(s', q')
        _current_v_sub_beta_sub_next_possible_v = {
            "lower": (current_v_safety.sub(_v) for _v in _beta_safety_add_next_possible_v["lower"]),
            "upper": (current_v_safety.sub(_v) for _v in _beta_safety_add_next_possible_v["upper"]),
        } # V_{safety}(s, q) - Beta_{safety} - V_{safety}(s', q')

        _inequalities_itr = zip(
            _current_v_sub_beta_sub_next_possible_v["lower"],
            _current_v_sub_beta_sub_next_possible_v["upper"]
        )
        _safety_inequalities = (
            [
                Inequality(
                    left_equation=_v_e_b_lower,
                    inequality_type=EquationConditionType.GREATER_THAN_OR_EQUAL,
                    right_equation=self.template_manager.variables.zero_eq
                ),
                Inequality(
                    left_equation=_v_e_b_upper,
                    inequality_type=EquationConditionType.GREATER_THAN_OR_EQUAL,
                    right_equation=self.template_manager.variables.zero_eq
                ),

                Inequality(
                    left_equation=_v_e_b_lower,
                    inequality_type=EquationConditionType.LESS_THAN_OR_EQUAL,
                    right_equation=self.template_manager.variables.delta_safe_eq
                ),
                Inequality(
                    left_equation=_v_e_b_upper,
                    inequality_type=EquationConditionType.LESS_THAN_OR_EQUAL,
                    right_equation=self.template_manager.variables.delta_safe_eq
                ),
            ]
            for _v_e_b_lower, _v_e_b_upper in _inequalities_itr
        )

        return [
            SubConstraint(
                expr_1=_sed, # X |= a & V_{safety}(s, q) >= E[V_{safety}(s', q')] + \epsilon_{Safety}
                # expr_2=_safety, # V_{safety}(s, q) - Beta_{safety} - V_{safety}(s', q') >= 0 & V_{safety}(s, q) - Beta_{safety} - V_{safety}(s', q') <= \delta_{Safety}
                aggregation_type=ConstraintAggregationType.CONJUNCTION
            )
            for _sed, _safety in zip(_guarded_sed, _safety_inequalities)
        ]


