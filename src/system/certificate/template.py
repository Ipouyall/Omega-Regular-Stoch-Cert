from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from ..polynomial.equation import Equation
from ..polynomial.polynomial import Monomial
from ..utils import power_generator


class CertificateTemplateType(Enum):
    REACH_AND_STAY = "reach_and_stay"
    BUCHI = "buchi"

    @classmethod
    def from_string(cls, template_type: str):
        if template_type not in cls.__members__:
            raise ValueError(f"Invalid template type: {template_type}.")
        return cls[template_type.upper()]

    def __str__(self):
        return f"{self.value.replace('_', ' ').replace('and','&').title():<12}"


@dataclass
class CertificateTemplate:
    state_dimension: int
    action_dimension: int
    abstraction_dimension: int
    maximal_polynomial_degree: int
    variable_generators: list[str]
    template_type: CertificateTemplateType
    buchi_id: Optional[int] = None  # only for Buchi templates
    templates: dict[str, Equation] = field(init=False, default_factory=dict)
    generated_constants: set[str] = field(init=False, default_factory=set)

    def __post_init__(self):
        if self.template_type == CertificateTemplateType.BUCHI and self.buchi_id is None:
            raise ValueError("Buchi templates must have a Buchi ID.")
        self._initialize_templates()

    def _initialize_templates(self):
        constant_signature = f"Vb{self.buchi_id}" if self.template_type == CertificateTemplateType.BUCHI else "Vrs"
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
            self.templates[str(i)] = _equation

            _new_consts = {f"{_pre}_{const_postfix}" for const_postfix, _ in cp_generator}  # TODO: This can be more optimized
            self.generated_constants.update(_new_consts)

    def get_generated_constants(self):
        return self.generated_constants

    def to_detailed_string(self):
        return f"{self.template_type} template (|S|={self.state_dimension}, |A|={self.action_dimension}, |Q|={self.abstraction_dimension}, degree={self.maximal_polynomial_degree})\n" + \
                "\n".join([f"  - {'(q'+key+')':<5}: {value}" for key, value in self.templates.items()])

    def __str__(self):
        return f"{self.template_type} template (|S|={self.state_dimension}, |A|={self.action_dimension}, |Q|={self.abstraction_dimension}, degree={self.maximal_polynomial_degree})"


@dataclass
class LTLCertificateDecomposedTemplates:
    state_dimension: int
    action_dimension: int
    abstraction_dimension: int
    maximal_polynomial_degree: int
    accepting_components_count: int
    buchi_templates: list[CertificateTemplate] = field(init=False, default_factory=list)
    reach_and_stay_template: CertificateTemplate = field(init=False, default_factory=list)
    variable_generators: list[str] = field(init=False, default_factory=list)
    generated_constants: set[str] = field(init=False, default_factory=set)

    def __post_init__(self):
        self.variable_generators = [f"S{i}" for i in range(1, self.state_dimension + 1)]
        self._initialize_templates()

    def _initialize_templates(self):
        self.reach_and_stay_template = CertificateTemplate(
            state_dimension=self.state_dimension,
            action_dimension=self.action_dimension,
            abstraction_dimension=self.abstraction_dimension,
            maximal_polynomial_degree=self.maximal_polynomial_degree,
            variable_generators=self.variable_generators,
            template_type=CertificateTemplateType.REACH_AND_STAY,
        )
        self.buchi_templates = [
            CertificateTemplate(
                state_dimension=self.state_dimension,
                action_dimension=self.action_dimension,
                abstraction_dimension=self.abstraction_dimension,
                maximal_polynomial_degree=self.maximal_polynomial_degree,
                variable_generators=self.variable_generators,
                template_type=CertificateTemplateType.BUCHI,
                buchi_id=i
            ) for i in range(self.accepting_components_count)
        ]
        self.generated_constants.update(self.reach_and_stay_template.get_generated_constants())
        for bt in self.buchi_templates:
            self.generated_constants.update(bt.get_generated_constants())

    def get_generated_constants(self):
        return self.generated_constants

    def __str__(self):
        return f"LTLCertificateDecomposedTemplates(Reach-and-Stay, {', '.join('Büchi-'+str(b.buchi_id) for b in self.buchi_templates)})\n" +\
            '\n'.join([f"    - {self.reach_and_stay_template}"]+ [f"    - {template}" for template in self.buchi_templates])
