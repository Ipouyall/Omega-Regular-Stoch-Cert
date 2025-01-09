from dataclasses import dataclass
from typing import List, Dict

from .constraint_inequality import ConstraintInequality, ConstraintAggregationType, SubConstraint, GuardedInequality
from .constraints import Constraint
from .invariant_template import InvariantTemplate
from ..action import SystemDecomposedControlPolicy, SystemControlPolicy, PolicyType
from ..automata.graph import Automata
from ..dynamics import SystemDynamics, ConditionalDynamics
from ..noise import SystemStochasticNoise
from ..polynomial.equation import Equation
from ..polynomial.inequality import EquationConditionType, Inequality
from ..space import SystemSpace


@dataclass
class InvariantInitialConstraint(Constraint):
    template: InvariantTemplate
    system_space: SystemSpace
    initial_space: SystemSpace
    automata: Automata

    __slots__ = ["template", "system_space", "initial_space", "automata"]

    def extract(self) -> list[ConstraintInequality]:
        _eq_zero = Equation.extract_equation_from_string("0")
        _initial_state = self.automata.start_state_id
        _ineq = Inequality(
            left_equation=self.template.templates[_initial_state],
            inequality_type=EquationConditionType.GREATER_THAN_OR_EQUAL,
            right_equation=_eq_zero
        )
        template_rhs = SubConstraint(
            expr_1=_ineq,
            aggregation_type=ConstraintAggregationType.CONJUNCTION
        )
        return [
            ConstraintInequality(
                variables=self.template.variable_generators,
                lhs=SubConstraint(
                    expr_1=self.system_space.space_inequalities + self.initial_space.space_inequalities,
                    aggregation_type=ConstraintAggregationType.CONJUNCTION),
                rhs=template_rhs,
            )
        ]


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
                eq_zero=eq_zero,
                disturbance_var_gens=disturbance_var_gens,
                disturbance_bounds_inequalities=disturbance_bounds_inequalities
            )
        return constraints

    def _extract_helper(
            self,
            constraints: list[ConstraintInequality],
            system_dynamics: ConditionalDynamics,
            eq_zero,
            disturbance_var_gens,
            disturbance_bounds_inequalities) -> list[ConstraintInequality]:

        for state in self.automata.states:
            current_i = self.template.templates[str(state.state_id)]
            next_state_condition, next_state = self._next_sds_state_helper(
                dynamical=system_dynamics,
                policy=self.decomposed_control_policy.get_policy(PolicyType.ACCEPTANCE)  # TODO: which policy?
            )

            _next_possible_q_ids = (t.destination for t in state.transitions)
            _next_possible_i_guards = (t.label for t in state.transitions)
            _next_possible_invariants = (self.template.templates[str(_q_id)] for _q_id in _next_possible_q_ids) #  INV(s, q')
            _next_possible_updated_invariants = (inv(**next_state).replace(" ", "") for inv in _next_possible_invariants) # INV(s', q')

            lhs_next_possible_i_guarded = [
                GuardedInequality(  # if transition (q to q') is possible
                    guard=_guard,  # the label of the transition
                    inequality=Inequality(
                        left_equation=current_i,
                        inequality_type=EquationConditionType.GREATER_THAN_OR_EQUAL,
                        right_equation=eq_zero
                    ),
                    aggregation_type=ConstraintAggregationType.CONJUNCTION,
                    lookup_table=self.automata.lookup_table,
                )
                for _guard in _next_possible_i_guards
            ]

            for next_possible_i_guarded, invariant_str in zip(lhs_next_possible_i_guarded,_next_possible_updated_invariants):
                _lhs = SubConstraint(
                    expr_1=self.system_space.space_inequalities+next_state_condition+[next_possible_i_guarded]+disturbance_bounds_inequalities,
                    aggregation_type=ConstraintAggregationType.CONJUNCTION
                )
                invariant_eq = Equation.extract_equation_from_string(invariant_str)
                _rhs_inequality = SubConstraint(
                    expr_1=Inequality(
                        left_equation=invariant_eq,
                        inequality_type=EquationConditionType.GREATER_THAN_OR_EQUAL,
                        right_equation=eq_zero
                    ),
                    aggregation_type=ConstraintAggregationType.CONJUNCTION
                )
                constraints.append(
                    ConstraintInequality(
                        variables=self.template.variable_generators+disturbance_var_gens,
                        lhs=_lhs,
                        rhs=_rhs_inequality
                    )
                )
        return constraints

    @staticmethod
    def _next_sds_state_helper(dynamical: ConditionalDynamics, policy: SystemControlPolicy) -> [List[Inequality], Dict[str, str]]:
        _action = policy()
        return dynamical.condition, dynamical(_action)

