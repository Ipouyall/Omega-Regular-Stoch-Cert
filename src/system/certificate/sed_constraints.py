from dataclasses import dataclass

from .constraint_inequality import ConstraintInequality, ConstraintAggregationType, GuardedInequality, SubConstraint
from .constraints import Constraint, _replace_keys_with_values
from .invariant_template import InvariantTemplate
from .template import LTLCertificateDecomposedTemplates
from ..action import SystemDecomposedControlPolicy, PolicyType
from ..automata.graph import Automata
from ..dynamics import SystemDynamics, ConditionalDynamics
from ..noise import SystemStochasticNoise
from ..polynomial.equation import Equation
from ..polynomial.inequality import EquationConditionType, Inequality
from ..space import SystemSpace


@dataclass
class StrictExpectedDecrease(Constraint):
    template_manager: LTLCertificateDecomposedTemplates
    invariant: InvariantTemplate
    system_space: SystemSpace
    decomposed_control_policy: SystemDecomposedControlPolicy
    disturbance: SystemStochasticNoise
    system_dynamics: SystemDynamics
    automata: Automata
    epsilon: float
    probability_threshold: float

    def extract(self) -> list[ConstraintInequality]:
        constraints = []
        self.extraxt_reach_and_stay(constraints=constraints)
        self.extract_buchi(constraints=constraints)
        return constraints

    __slots__ = [
        "template_manager", "system_space", "invariant", "decomposed_control_policy",
        "disturbance", "system_dynamics", "automata", "epsilon", "probability_threshold"
    ]

    def extraxt_reach_and_stay(self, constraints):
        _p = Equation.extract_equation_from_string(f"1/(1-{self.probability_threshold})")
        _eq_epsilon = Equation.extract_equation_from_string(str(self.epsilon))
        _eq_zero = Equation.extract_equation_from_string("0")

        for dynamical in self.system_dynamics.system_transformations:
            self.extraxt_reach_and_stay_helper(
                constraints=constraints,
                _p=_p,
                _eq_epsilon=_eq_epsilon,
                _eq_zero=_eq_zero,
                system_dynamics=dynamical,
            )

    def extraxt_reach_and_stay_helper(self,constraints,_p,_eq_epsilon,_eq_zero,system_dynamics: ConditionalDynamics) -> list[ConstraintInequality]:
        """
        forall S and q ∈ Q/Qt, [1/(1-p) - V^{reach-and-stay}(s,q) >= 0] → [V^{reach-and-stay}(s,q) − E[V^{reach-and-stay}(s',q')] − ϵ ≥ 0]
        """
        #  S' under π_accept
        _s_control_policy_accept = self.decomposed_control_policy.get_policy(PolicyType.ACCEPTANCE)
        _s_control_action_accept = _s_control_policy_accept()
        _s_next_states_under_accept = system_dynamics(_s_control_action_accept)  # Dict: {state_id: StringEquation}

        for _q_id in range(self.template_manager.abstraction_dimension):
            q = self.automata.get_state(_q_id)
            # q ∈ Q/Qt
            if q.is_accepting():
                continue

            #  V(s,q) <= 1/(1-p) == 1/(1-p) - V(s,q) >= 0
            current_v = self.template_manager.reach_and_stay_template.templates[str(_q_id)]
            _left_land_side = Inequality(
                left_equation=_p.sub(current_v),
                inequality_type=EquationConditionType.GREATER_THAN_OR_EQUAL,
                right_equation=_eq_zero
            )

            #  V(s, q')
            next_possible_q_ids = (t.destination for t in q.transitions)
            next_possible_v_guards = (t.label for t in q.transitions)
            next_possible_v = (
                self.template_manager.reach_and_stay_template.templates[str(_q_id)]
                for _q_id in next_possible_q_ids
            )

            #  V(s', q')
            possible_next_vs = (
                _v(**_s_next_states_under_accept).replace(" ", "")
                for _v in next_possible_v
            )

            # E[V(s',q')]
            disturbance_expectations = self.disturbance.get_expectations()
            expected_possible_next_vs = (
                _replace_keys_with_values(_v, disturbance_expectations)
                for _v in possible_next_vs
            )
            expected_next_v_eq = (
                Equation.extract_equation_from_string(_v)
                for _v in expected_possible_next_vs
            )

            # V(s,q) − ϵ
            _t = current_v.sub(_eq_epsilon)

            # V(s,q) − E[V(s',q')] − ϵ
            _t_right_hand_sides = (
                _t.sub(_expected_v)
                for _expected_v in expected_next_v_eq
            )
            _right_hand_sides = [
                GuardedInequality(  # if transition (q to q') is possible, then:  V(s,q) − E[V(s',q')] − ϵ ≥ 0
                    guard=_guard,  # the label of the transition
                    inequality=Inequality(  # V(s,q) − E[V(s',q')] − ϵ ≥ 0
                        left_equation=_lhs,
                        inequality_type=EquationConditionType.GREATER_THAN_OR_EQUAL,
                        right_equation=_eq_zero
                    ),
                    aggregation_type=ConstraintAggregationType.CONJUNCTION,
                    lookup_table=self.automata.lookup_table,
                )
                for _lhs, _guard in zip(_t_right_hand_sides, next_possible_v_guards)
            ]
            constraints.append(
                ConstraintInequality(  # [1/(1-p) - V(s,q) >= 0] → [V(s,q) − E[V(s',q')] − ϵ ≥ 0]
                    variables=self.template_manager.variable_generators,
                    lhs=SubConstraint(
                        expr_2=self.system_space.space_inequalities+system_dynamics.condition,
                        expr_1=[_left_land_side, self.invariant.get_lhs_invariant(str(_q_id))],
                        aggregation_type=ConstraintAggregationType.CONJUNCTION),
                    rhs=SubConstraint(expr_1=_right_hand_sides, aggregation_type=ConstraintAggregationType.DISJUNCTION),
                )
            )
        return constraints

    def extract_buchi(self, constraints):
        _p = Equation.extract_equation_from_string(f"1/(1-{self.probability_threshold})")
        _eq_epsilon = Equation.extract_equation_from_string(str(self.epsilon))
        _eq_zero = Equation.extract_equation_from_string("0")

        for dynamical in self.system_dynamics.system_transformations:
            self.extract_buchi_helper(
                constraints=constraints,
                _p=_p,
                _eq_epsilon=_eq_epsilon,
                _eq_zero=_eq_zero,
                system_dynamics=dynamical,
            )

    def extract_buchi_helper(
            self,
            constraints,
            _p,
            _eq_epsilon,
            _eq_zero,
            system_dynamics,
    ) -> list[ConstraintInequality]:
        """
        Strict expected decrease in V^{Büchi i} and non-strict expected decrease in V^{reach-and-stay} under π^{buchi}_{i}:
        forall S and q ∈ Q_{accept}/F_{i}, [1/(1-p) - V^{reach-and-stay}(s,q) >= 0] → [V^{buchi i}(s,q) − E[V^{buchi i}(s',q')] − ϵ ≥ 0] and [V^{reach-and-stay}(s,q) − E[V^{reach-and-stay}(s',q')] ≥ 0]
        """
        buchi_counts = self.decomposed_control_policy.get_length()[PolicyType.BUCHI]
        for _buchi_id in range(buchi_counts):  # for each buchi i
            _buchi_control_policy = self.decomposed_control_policy.get_policy(PolicyType.BUCHI,_buchi_id)  # π^{buchi}_{i}
            _s_control_action_buchi = _buchi_control_policy()
            _s_next_states_under_buchi = system_dynamics(_s_control_action_buchi)

            for _q_id in range(self.template_manager.abstraction_dimension):
                q = self.automata.get_state(_q_id)
                # q ∈ Q_{accept}/F_{i}
                if q.is_accepting() and not q.is_in_accepting_signature(_buchi_id):
                    pass
                else:
                    continue

                #  V^{reach-and-stay}(s,q) <= 1/(1-p) == 1/(1-p) - V^{reach-and-stay}(s,q) >= 0
                current_v_reach_and_stay = self.template_manager.reach_and_stay_template.templates[str(_q_id)]
                _left_land_side = Inequality(
                    left_equation=_p.sub(current_v_reach_and_stay),
                    inequality_type=EquationConditionType.GREATER_THAN_OR_EQUAL,
                    right_equation=_eq_zero
                )

                #  V^{reach-and-stay}(s, q')
                next_possible_q_ids = [t.destination for t in q.transitions]
                next_possible_v_guards = (t.label for t in q.transitions)
                next_possible_v_reach_and_stay = [
                    self.template_manager.reach_and_stay_template.templates[str(_q_id)]
                    for _q_id in next_possible_q_ids
                ]
                #  V^{reach-and-stay}(s', q')
                possible_next_vs_reach_and_stay = (
                    _v(**_s_next_states_under_buchi).replace(" ", "")
                    for _v in next_possible_v_reach_and_stay
                )
                # E[V^{reach-and-stay}(s',q')]
                disturbance_expectations = self.disturbance.get_expectations()
                expected_possible_next_vs_reach_and_stay = (
                    _replace_keys_with_values(_v, disturbance_expectations)
                    for _v in possible_next_vs_reach_and_stay
                )
                expected_next_v_eq_reach_and_stay = (
                    Equation.extract_equation_from_string(_v)
                    for _v in expected_possible_next_vs_reach_and_stay
                )
                # V^{reach-and-stay}(s,q) − E[V^{reach-and-stay}(s',q')
                _t_right_hand_sides_reach_and_stay = (
                    current_v_reach_and_stay.sub(_expected_v)
                    for _expected_v in expected_next_v_eq_reach_and_stay
                )
                # V^{reach-and-stay}(s,q) − E[V^{reach-and-stay}(s',q')] ≥ 0
                _rhs_reach_and_stay = (
                    Inequality(
                        left_equation=_lhs,
                        inequality_type=EquationConditionType.GREATER_THAN_OR_EQUAL,
                        right_equation=_eq_zero
                    )
                    for _lhs in _t_right_hand_sides_reach_and_stay
                )

                #  V^{buchi i}(s,q)
                current_v_buchi = self.template_manager.buchi_templates[_buchi_id].templates[str(_q_id)]
                # V^{buchi i}(s, q')
                next_possible_v_buchi = (
                    self.template_manager.buchi_templates[_buchi_id].templates[str(_q_id)]
                    for _q_id in next_possible_q_ids
                )
                #  V^{buchi i}(s', q')
                possible_next_vs_buchi = (
                    _v(**_s_next_states_under_buchi).replace(" ", "")
                    for _v in next_possible_v_buchi
                )
                # E[V^{buchi i}(s',q')]
                expected_possible_next_vs_buchi = (
                    _replace_keys_with_values(_v, disturbance_expectations)
                    for _v in possible_next_vs_buchi
                )
                expected_next_v_eq_buchi = (
                    Equation.extract_equation_from_string(_v)
                    for _v in expected_possible_next_vs_buchi
                )
                # V^{buchi i}(s,q) − ϵ
                _t_buchi = current_v_buchi.sub(_eq_epsilon)
                # V^{buchi i}(s,q) − E[V^{buchi i}(s',q')] − ϵ
                _t_right_hand_sides_buchi = (
                    _t_buchi.sub(_expected_v)
                    for _expected_v in expected_next_v_eq_buchi
                )
                # V^{buchi i}(s,q) − E[V^{buchi i}(s',q')] − ϵ ≥ 0
                _right_hand_sides_buchi = (
                    Inequality(
                        left_equation=_lhs,
                        inequality_type=EquationConditionType.GREATER_THAN_OR_EQUAL,
                        right_equation=_eq_zero
                    )
                    for _lhs in _t_right_hand_sides_buchi
                )

                # if transition (q to q') is possible, then:  V^{reach-and-stay}(s,q) − E[V^{reach-and-stay}(s',q')] ≥ 0
                _rhs_buchi = (
                    GuardedInequality(
                        guard=_guard,
                        inequality=_ineq,
                        lookup_table=self.automata.lookup_table,
                    )
                    for _ineq, _guard in zip(_right_hand_sides_buchi, next_possible_v_guards)
                )

                # [V^{buchi i}(s,q) − E[V^{buchi i}(s',q')] − ϵ ≥ 0] and [V^{reach-and-stay}(s,q) − E[V^{reach-and-stay}(s',q')] ≥ 0]
                _rhs = [
                    SubConstraint(
                        expr_1=_buch,
                        expr_2=_reach,
                        aggregation_type=ConstraintAggregationType.CONJUNCTION
                    )
                    for _buch, _reach in zip(_rhs_buchi, _rhs_reach_and_stay)
                ]

                constraints.append(
                    ConstraintInequality(
                        variables=self.template_manager.variable_generators,
                        lhs=SubConstraint(
                            expr_2=self.system_space.space_inequalities+system_dynamics.condition,
                            expr_1=[_left_land_side, self.invariant.get_lhs_invariant(str(_q_id))],
                            aggregation_type=ConstraintAggregationType.CONJUNCTION),
                        rhs=SubConstraint(expr_1=_rhs, aggregation_type=ConstraintAggregationType.DISJUNCTION),
                    )
                )

        return constraints
