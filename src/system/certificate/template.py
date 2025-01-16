from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from sympy import log, Pow

from ..polynomial.equation import Equation
from ..polynomial.polynomial import Monomial
from ..utils import power_generator


class CertificateTemplateType(Enum):
    REACH = "reach"
    SAFE = "safe"
    BUCHI = "buchi"

    def get_signature(self) -> str:
        return f"V_{self.value.lower()}"

    @classmethod
    def from_string(cls, template_type: str):
        if template_type not in cls.__members__:
            raise ValueError(f"Invalid template type: {template_type}.")
        return cls[template_type.upper()]

    def __str__(self):
        return f"{self.value.title():<5}"


@dataclass
class CertificateTemplate:
    state_dimension: int
    action_dimension: int
    abstraction_dimension: int
    maximal_polynomial_degree: int
    variable_generators: list[str]
    template_type: CertificateTemplateType
    instance_id: Optional[int] = None  # only for Buchi templates in LDGBA mode
    sub_templates: dict[str, Equation] = field(init=False, default_factory=dict)
    generated_constants: set[str] = field(init=False, default_factory=set)

    def __post_init__(self):
        if self.template_type in [CertificateTemplateType.BUCHI] and self.instance_id is None:
            raise ValueError(f"{self.template_type} template requires an instance_id.")
        self._initialize_templates()

    def _initialize_templates(self):
        constant_signature = self.template_type.get_signature() + (str(self.instance_id) if self.instance_id is not None else "")
        cp_generator = power_generator(
            poly_max_degree=self.maximal_polynomial_degree,
            variable_generators=self.state_dimension,
        )

        for i in range(self.abstraction_dimension):
            _pre = f"{constant_signature}_{i}"
            _monomials = [
                Monomial(
                    coefficient=1,
                    variable_generators=self.variable_generators + [f"{_pre}_{const_postfix}"],
                    power=powers + (1,)
                ) for (const_postfix, powers) in cp_generator
            ]
            _equation = Equation(monomials=_monomials)
            self.sub_templates[str(i)] = _equation
            self.generated_constants.update({f"{_pre}_{const_postfix}" for const_postfix, _ in cp_generator})

    def get_generated_constants(self):
        return self.generated_constants

    def to_detailed_string(self):
        return str(self) + "\n" + "\n".join([f"  - (q{key:<2}): {value}" for key, value in self.sub_templates.items()])

    def __str__(self):
        return f"Template(V={self.template_type}, |S|={self.state_dimension}, |A|={self.action_dimension}, |Q|={self.abstraction_dimension}, |C|={len(self.generated_constants):<3}, deg={self.maximal_polynomial_degree})"


@dataclass
class CertificateVariables:
    probability_threshold: float
    epsilon_safe: float  # Recommended as 0.1
    delta_safe: float  # Recommended as 1
    eta_safe: float = field(init=False)  # Recommended as [1/(8*epsilon_safe)*(delta_safe^2)*ceil(log(p))]
    epsilon_reach: float = field(init=False, default=1e-15)
    epsilon_buchi: float = field(init=False, default=1e-15)
    delta_buchi: float = field(init=False, default=1e-15)


    eta_safe_eq: Equation = field(init=False)
    Beta_safe_eq: Equation = field(init=False)
    zero_eq: Equation = field(init=False)

    generated_constants: set[str] = field(init=False, default_factory=set)


    epsilon_safe_eq: Equation = field(init=False)
    delta_safe_eq: Equation = field(init=False)
    epsilon_reach_eq: Equation = field(init=False)
    epsilon_buchi_eq: Equation = field(init=False)
    delta_buchi_eq: Equation = field(init=False)

    def __post_init__(self):
        assert self.epsilon_reach > 0, "Epsilon for reachability should be greater than 0."
        assert self.epsilon_buchi > 0, "Epsilon for Buchi should be greater than 0."
        assert self.epsilon_safe > 0, "Epsilon for safety should be greater than 0."
        assert self.delta_safe > 0, "Delta for safety should be greater than 0."
        assert self.delta_buchi > 0, "Delta for Buchi should be greater than 0."
        assert 1 > self.probability_threshold >= 0, "Probability threshold should be in the range [0, 1)."
        min_eta = 1e-10 + Pow(self.delta_safe,2)*log(1-self.probability_threshold)/(8*self.epsilon_safe)*(self.delta_safe**2)
        self.eta_safe = min_eta.evalf(n=10)
        assert self.eta_safe <= 0, f"Eta for safety should be less than or equal to 0. Got {self.eta_safe}."

        self.epsilon_safe_eq = Equation.extract_equation_from_string(f"{self.epsilon_safe}")
        self.delta_safe_eq = Equation.extract_equation_from_string(f"{self.delta_safe}")
        self.eta_safe_eq = Equation.extract_equation_from_string(f"{self.eta_safe}")
        self.epsilon_reach_eq = Equation.extract_equation_from_string(f"{self.epsilon_reach}")
        self.epsilon_buchi_eq = Equation.extract_equation_from_string(f"{self.epsilon_buchi}")
        self.delta_buchi_eq = Equation.extract_equation_from_string(f"{self.delta_buchi}")

        beta_safe_symbol = "Beta_safe"
        self.Beta_safe_eq = Equation.extract_equation_from_string(beta_safe_symbol)
        self.generated_constants.add(beta_safe_symbol)
        self.zero_eq = Equation.extract_equation_from_string("0")


@dataclass
class LTLCertificateDecomposedTemplates:
    state_dimension: int
    action_dimension: int
    abstraction_dimension: int
    maximal_polynomial_degree: int
    accepting_components_count: int
    variables: CertificateVariables
    buchi_template: CertificateTemplate = field(init=False)
    reach_template: CertificateTemplate = field(init=False)
    safe_template: CertificateTemplate = field(init=False)
    variable_generators: list[str] = field(init=False, default_factory=list)
    generated_constants: set[str] = field(init=False, default_factory=set)

    def __post_init__(self):
        self.variable_generators = [f"S{i}" for i in range(1, self.state_dimension + 1)]
        self._initialize_templates()
        self.generated_constants.update(self.variables.generated_constants)

    def _initialize_templates(self):
        self.reach_template = CertificateTemplate(
            state_dimension=self.state_dimension,
            action_dimension=self.action_dimension,
            abstraction_dimension=self.abstraction_dimension,
            maximal_polynomial_degree=self.maximal_polynomial_degree,
            variable_generators=self.variable_generators,
            template_type=CertificateTemplateType.REACH,
        )
        self.buchi_template = CertificateTemplate(
            state_dimension=self.state_dimension,
            action_dimension=self.action_dimension,
            abstraction_dimension=self.abstraction_dimension,
            maximal_polynomial_degree=self.maximal_polynomial_degree,
            variable_generators=self.variable_generators,
            template_type=CertificateTemplateType.BUCHI,
            instance_id=0
        )
        self.safe_template = CertificateTemplate(
            state_dimension=self.state_dimension,
            action_dimension=self.action_dimension,
            abstraction_dimension=self.abstraction_dimension,
            maximal_polynomial_degree=self.maximal_polynomial_degree,
            variable_generators=self.variable_generators,
            template_type=CertificateTemplateType.SAFE,
        )
        self.generated_constants.update(self.reach_template.get_generated_constants())
        self.generated_constants.update(self.safe_template.get_generated_constants())
        self.generated_constants.update(self.buchi_template.get_generated_constants())

    def get_generated_constants(self):
        return self.generated_constants

    def add_new_constant(self, constant: str):
        self.generated_constants.add(constant)

    def __str__(self):
        return (f"Certificate(|S|={self.state_dimension}, |A|={self.action_dimension}, |Q|={self.abstraction_dimension}, |F|={self.accepting_components_count}, |C|={len(self.generated_constants):<3}, deg={self.maximal_polynomial_degree})\n" +
                f"\t-{self.reach_template}\n" +
                f"\t-{self.safe_template}\n" +
                f"\t-{self.buchi_template}")
