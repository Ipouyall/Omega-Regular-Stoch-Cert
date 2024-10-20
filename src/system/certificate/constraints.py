from abc import ABC, abstractmethod
from dataclasses import dataclass
import re

from .constraint_inequality import ConstraintInequality, ConstraintAggregationType, GuardedInequality, SubConstraint
from .template import LTLCertificateDecomposedTemplates
from ..action import SystemDecomposedControlPolicy, PolicyType
from ..automata.graph import Automata
from ..dynamics import SystemDynamics
from ..polynomial.equation import Equation
from ..polynomial.inequality import EquationConditionType, Inequality



class Constraint(ABC):
    @abstractmethod
    def extract(self) -> list[ConstraintInequality]:
        pass


def _replace_keys_with_values(s, dictionary):
    pattern = re.compile("|".join(re.escape(key) for key in dictionary.keys()))
    result = pattern.sub(lambda match: dictionary[match.group(0)], s)
    return result


@dataclass
class NonNegativityConstraint(Constraint):
    """
    forall s ∈ R → V(s,q) ≥ 0
    """
    template_manager: LTLCertificateDecomposedTemplates

    __slots__ = ["template_manager"]

    def extraxt_reach_and_stay(self) -> list[ConstraintInequality]:
        _ineq = [
            Inequality(
                left_equation=t,
                inequality_type=EquationConditionType.GREATER_THAN_OR_EQUAL,
                right_equation=Equation.extract_equation_from_string("0")
            )
            for t in self.template_manager.reach_and_stay_template.templates.values()
        ]
        _sub = SubConstraint(
            expr_1=_ineq,
            aggregation_type=ConstraintAggregationType.CONJUNCTION
        )
        return [
            ConstraintInequality(
                variables=self.template_manager.variable_generators,
                lhs=None,
                rhs=_sub,
            )
        ]

    def extract_buchi(self) -> list[ConstraintInequality]:
        _inequalities = [
            [Inequality(
                left_equation=t,
                inequality_type=EquationConditionType.GREATER_THAN_OR_EQUAL,
                right_equation=Equation.extract_equation_from_string("0")
            ) for t in bt.templates.values()]
            for bt in self.template_manager.buchi_templates
        ]
        return [
            ConstraintInequality(
                variables=self.template_manager.variable_generators,
                lhs=None,
                rhs=SubConstraint(expr_1=_ineq, aggregation_type=ConstraintAggregationType.CONJUNCTION),
            )
            for _ineq in _inequalities
        ]


    def extract(self) -> list[ConstraintInequality]:
        return self.extraxt_reach_and_stay() + self.extract_buchi()


@dataclass
class StrictExpectedDecrease(Constraint):
    template_manager: LTLCertificateDecomposedTemplates
    decomposed_control_policy: SystemDecomposedControlPolicy
    system_dynamics: SystemDynamics
    automata: Automata
    epsilon: float
    probability_threshold: float

    __slots__ = ["template_manager", "decomposed_control_policy", "automata", "epsilon", "probability_threshold"]

    def extraxt_reach_and_stay(self) -> list[ConstraintInequality]:
        """
        forall S and q ∈ Q/Qt, [1/(1-p) - V(s,q) >= 0] → [V(s,q) − E[V(s',q')] − ϵ ≥ 0]
        """
        constraints = []
        _p = Equation.extract_equation_from_string(f"1/(1-{self.probability_threshold})")
        _eq_epsilon = Equation.extract_equation_from_string(str(self.epsilon))
        _eq_zero = Equation.extract_equation_from_string("0")

        _s_ra_control_policy_accept = self.decomposed_control_policy.get_policy(PolicyType.ACCEPTANCE)
        _s_control_action_accept = _s_ra_control_policy_accept()
        _s_next_states_under_accept = self.system_dynamics(_s_control_action_accept)  # Dict: {state_id: StringEquation}

        for _q_id in range(self.template_manager.abstraction_dimension):
            q = self.automata.get_state(str(_q_id))
            if q.is_accepting():
                continue
            current_v = self.template_manager.reach_and_stay_template.templates[str(_q_id)]
            _left_land_side = Inequality(
                left_equation=_p.sub(current_v),
                inequality_type=EquationConditionType.GREATER_THAN_OR_EQUAL,
                right_equation=_eq_zero
            )

            next_possible_q_ids = (t.destination_id for t in q.transitions)
            next_possible_v_guards = (t.predicate for t in q.transitions)
            next_possible_v = [
                self.template_manager.reach_and_stay_template.templates[str(_q_id)]
                for _q_id in next_possible_q_ids
            ]

            possible_next_vs = [
                _v(**_s_next_states_under_accept).replace(" ", "")
                for _v in next_possible_v
            ]
            # TODO: add disturbance expectation here
            #       Convert each string equation to Equation, to be expanded
            #       Then consider sample code below
            # disturbance_expectations = Get are the disturbances, then
            # refined_disturbance_expectations = {
            #     f"D{dim + 1}**{i}": str(d)
            #     for dim in range(self.system_disturbance.dimension)
            #     for i, d in enumerate(disturbance_expectations[dim], start=1)
            # }
            # for dim in range(self.system_disturbance.dimension):
            #     refined_disturbance_expectations[f"D{dim + 1}"] = str(disturbance_expectations[dim][0])
            # _v_next = _replace_keys_with_values(_v_next, refined_disturbance_expectations)
            expected_next_v_eq = [
                Equation.extract_equation_from_string(_v)
                for _v in possible_next_vs
            ]
            _t = current_v.sub(_eq_epsilon)
            _t_right_hand_sides = [
                _t.sub(_expected_v)
                for _expected_v in expected_next_v_eq
            ]
            _right_hand_sides = [
                GuardedInequality(
                    guard=_guard,
                    inequality=Inequality(
                        left_equation=_lhs,
                        inequality_type=EquationConditionType.GREATER_THAN_OR_EQUAL,
                        right_equation=_eq_zero
                    ),
                    aggregation_type=ConstraintAggregationType.CONJUNCTION
                )
                for _lhs, _guard in zip(_t_right_hand_sides, next_possible_v_guards)
            ]
            constraints.append(
                ConstraintInequality(
                    variables=self.template_manager.variable_generators,
                    lhs=SubConstraint(expr_1=_left_land_side),
                    rhs=SubConstraint(expr_1=_right_hand_sides, aggregation_type=ConstraintAggregationType.DISJUNCTION),
                )
            )
        return constraints

    def extract_buchi(self) -> list[ConstraintInequality]:
        print("NOTE! Extracting Strict Expected Decrease Constraints for buchi hasn't implemented yet")
        return []


    def extract(self) -> list[ConstraintInequality]:
        return self.extraxt_reach_and_stay() + self.extract_buchi()


@dataclass
class NonStrictExpectedDecrease(Constraint):
    template_manager: LTLCertificateDecomposedTemplates
    decomposed_control_policy: SystemDecomposedControlPolicy
    system_dynamics: SystemDynamics
    automata: Automata
    epsilon: float
    probability_threshold: float

    __slots__ = ["template_manager", "decomposed_control_policy", "automata", "epsilon", "probability_threshold"]

    def extraxt_reach_and_stay(self) -> list[ConstraintInequality]:
        """
        forall S and q ∈ Q_{acc}, [1/(1-p) - V(s,q) >= 0] → [V(s,q) − E[V(s',q')]≥ 0]
        """
        constraints = []
        _p = Equation.extract_equation_from_string(f"1/(1-{self.probability_threshold})")
        _eq_zero = Equation.extract_equation_from_string("0")

        _s_ra_control_policy_accept = self.decomposed_control_policy.get_policy(PolicyType.ACCEPTANCE)
        _s_control_action_accept = _s_ra_control_policy_accept()
        _s_next_states_under_accept = self.system_dynamics(_s_control_action_accept)  # Dict: {state_id: StringEquation}

        for _q_id in range(self.template_manager.abstraction_dimension):
            q = self.automata.get_state(str(_q_id))
            if not q.is_accepting():
                continue
            current_v = self.template_manager.reach_and_stay_template.templates[str(_q_id)]
            _left_land_side = Inequality(
                left_equation=_p.sub(current_v),
                inequality_type=EquationConditionType.GREATER_THAN_OR_EQUAL,
                right_equation=_eq_zero
            )

            next_possible_q_ids = (t.destination_id for t in q.transitions)
            next_possible_v_guards = (t.predicate for t in q.transitions)
            next_possible_v = [
                self.template_manager.reach_and_stay_template.templates[str(_q_id)]
                for _q_id in next_possible_q_ids
            ]

            possible_next_vs = [
                _v(**_s_next_states_under_accept).replace(" ", "")
                for _v in next_possible_v
            ]
            # TODO: add disturbance expectation here
            #       Convert each string equation to Equation, to be expanded
            #       Then consider sample code below
            # disturbance_expectations = Get are the disturbances, then
            # refined_disturbance_expectations = {
            #     f"D{dim + 1}**{i}": str(d)
            #     for dim in range(self.system_disturbance.dimension)
            #     for i, d in enumerate(disturbance_expectations[dim], start=1)
            # }
            # for dim in range(self.system_disturbance.dimension):
            #     refined_disturbance_expectations[f"D{dim + 1}"] = str(disturbance_expectations[dim][0])
            # _v_next = _replace_keys_with_values(_v_next, refined_disturbance_expectations)
            expected_next_v_eq = [
                Equation.extract_equation_from_string(_v)
                for _v in possible_next_vs
            ]
            _t_right_hand_sides = [
                current_v.sub(_expected_v)
                for _expected_v in expected_next_v_eq
            ]
            _right_hand_sides = [
                GuardedInequality(
                    guard=_guard,
                    inequality=Inequality(
                        left_equation=_lhs,
                        inequality_type=EquationConditionType.GREATER_THAN_OR_EQUAL,
                        right_equation=_eq_zero
                    ),
                    aggregation_type=ConstraintAggregationType.CONJUNCTION
                )
                for _lhs, _guard in zip(_t_right_hand_sides, next_possible_v_guards)
            ]
            constraints.append(
                ConstraintInequality(
                    variables=self.template_manager.variable_generators,
                    lhs=SubConstraint(expr_1=_left_land_side),
                    rhs=SubConstraint(expr_1=_right_hand_sides, aggregation_type=ConstraintAggregationType.DISJUNCTION),
                )
            )
        return constraints

    def extract_buchi(self) -> list[ConstraintInequality]:
        print("NOTE! Extracting Non-Strict Expected Decrease Constraints for buchi hasn't implemented yet")
        return []


    def extract(self) -> list[ConstraintInequality]:
        return self.extraxt_reach_and_stay() + self.extract_buchi()


