from dataclasses import dataclass, field

from ...polynomial.equation import Equation
from ...polynomial.inequality import Inequality, EquationConditionType
from ...polynomial.polynomial import Monomial
from ...utils import power_generator


@dataclass
class InvariantTemplate:
    state_dimension: int
    action_dimension: int
    abstraction_dimension: int
    maximal_polynomial_degree: int
    variable_generators: list[str] = field(init=False, default_factory=list)
    templates: dict[str, Equation] = field(init=False, default_factory=dict)
    generated_constants: set[str]  = field(init=False, default_factory=set)

    def __post_init__(self):
        self.variable_generators = [f"S{i}" for i in range(1, self.state_dimension + 1)]
        self._initialize_templates()

    def _initialize_templates(self):
        cp_generator = power_generator(
            poly_max_degree=self.maximal_polynomial_degree,
            variable_generators=self.state_dimension,
        )

        for i in range(self.abstraction_dimension):
            _pre = f"I_{i}"
            _monomials = [
                Monomial(
                    coefficient=1,
                    variable_generators=self.variable_generators + [f"{_pre}_{const_postfix}"],
                    power=powers + (1,)
                ) for (const_postfix, powers) in cp_generator
            ]
            _equation = Equation(monomials=_monomials)
            self.templates[str(i)] = _equation

            _new_consts = {f"{_pre}_{const_postfix}" for const_postfix, _ in cp_generator}
            self.generated_constants.update(_new_consts)

    def get_generated_constants(self):
        return self.generated_constants

    def get_lhs_invariant(self, q: str) -> Inequality:
        return Inequality(
            left_equation=self.templates[q],
            inequality_type=EquationConditionType.GREATER_THAN_OR_EQUAL,
            right_equation=Equation.extract_equation_from_string("0"),
        )

    def to_detailed_string(self):
        return f"{str(self)}\n" + "\n".join([f"  - {'(q'+key+')':<5}: {value}" for key, value in self.templates.items()])

    def __str__(self):
        return f"Invariant(|S|={self.state_dimension}, |A|={self.action_dimension}, |Q|={self.abstraction_dimension}, degree={self.maximal_polynomial_degree})"


@dataclass
class InvariantFakeTemplate:

    def __post_init__(self):
        self.fake_lhs_invariant = Inequality(
            left_equation=Equation.extract_equation_from_string("1"),
            inequality_type=EquationConditionType.GREATER_THAN_OR_EQUAL,
            right_equation=Equation.extract_equation_from_string("0"),
        )

    @staticmethod
    def get_generated_constants():
        return set()

    def get_lhs_invariant(self, q: str) -> Inequality:
        return self.fake_lhs_invariant
