from dataclasses import dataclass

from .constraint import ConstraintInequality, ConstraintAggregationType, SubConstraint
from .constraintI import Constraint
from .template import LTLCertificateDecomposedTemplates
from ..automata.graph import Automata
from ..polynomial.equation import Equation
from ..polynomial.inequality import EquationConditionType, Inequality
from ..space import SystemSpace


@dataclass
class InitialSpaceConstraint(Constraint):
    template_manager: LTLCertificateDecomposedTemplates
    system_space: SystemSpace
    initial_space: SystemSpace
    automata: Automata

    def extract(self) -> list[ConstraintInequality]:
        constraints = []
        self.extraxt_reach_and_stay(constraints=constraints)
        return constraints

    __slots__ = ["template_manager", "system_space", "automata"]

    def extraxt_reach_and_stay(self, constraints):
        """
        forall s in system_space.  s in InitRegion => V^{reach-and-stay}(s,q_init) <= 1
        Here, q_init is the initial state of the automaton
        """
        _eq_one = Equation.extract_equation_from_string("1")
        _initial_state = self.automata.start_state_id
        _ineq = Inequality(
            left_equation=self.template_manager.reach_template.decomposed_sub_templates[str(_initial_state)],
            inequality_type=EquationConditionType.LESS_THAN_OR_EQUAL,
            right_equation=_eq_one
        )
        template_rs_bound = SubConstraint(
            expr_1=_ineq,
            aggregation_type=ConstraintAggregationType.CONJUNCTION
        )

        constraints.append(
            ConstraintInequality(
                variables=self.template_manager.variable_generators,
                lhs=SubConstraint(
                    expr_1=self.system_space.space_inequalities + self.initial_space.space_inequalities,
                    aggregation_type=ConstraintAggregationType.CONJUNCTION),
                rhs=template_rs_bound,
            )
        )

        return constraints

    # def extract_buchi(self, constraints):
    #     return
