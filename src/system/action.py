from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum
from numbers import Number
from typing import Sequence, Union, Dict

from . import logger
from .polynomial.equation import Equation
from .polynomial.polynomial import Monomial
from .utils import power_generator


class PolicyMode(Enum):
    VERIFICATION = "verification"
    SYNTHESIS = "synthesis"

    @classmethod
    def from_string(cls, mode: str):
        if mode not in cls.__members__:
            raise ValueError(f"Invalid policy mode: {mode}.")
        return cls[mode.upper()]

    def __str__(self):
        return self.value


class PolicyType(Enum):
    ACCEPTANCE = "acceptance"
    BUCHI = "buchi"
    UNKOWN = "unknown"

    @classmethod
    def from_string(cls, policy_type: str):
        if policy_type not in cls.__members__:
            raise ValueError(f"Invalid policy type: {policy_type}.")
        return cls[policy_type.upper()]

    def __str__(self):
        return f"{self.value:<10}"


@dataclass
class SystemControlAction:
    action_values: Sequence[Number]
    dimension: int

    __slots__ = ["action_values", "dimension"]

    def __post_init__(self):
        if self.dimension is None:
            logger.warning("The dimension of the action space has not been set. Attempting to infer the dimension from the number of action values.")
            self.dimension = len(self.action_values)
        if len(self.action_values) != self.dimension:
            logger.warning(f"The number of action values does not match the dimension of the action space \
            ({len(self.action_values)} != {self.dimension}). Correcting the dimension based on the number of action values.")

        if self.dimension == 0:
            raise ValueError("The dimension of the action space must be greater than 0.")

    def __call__(self, *args, **kwargs):
        return {
            f"A{i}": p for i, p in enumerate(self.action_values, start=1)
        }

    def __str__(self):
        return f"Action π{self.dimension}: {self.action_values}"


@dataclass
class SystemControlPolicy:
    action_dimension: int
    state_dimension: int
    maximal_degree: int
    transitions: Union[None, Sequence[Equation]] = None
    prefix: str = ""
    type: PolicyType = PolicyType.UNKOWN
    mode: PolicyMode = field(init=False, default=PolicyMode.SYNTHESIS)
    generated_constants: set[str] = field(init=False, default_factory=set)
    constants_founded: bool = field(init=False, default=False)

    def __post_init__(self):
        if self.transitions is not None and len(self.transitions) != self.action_dimension:
            logger.error(f"No valid control policy provided. Ignoring the provided policy.")
            logger.info(f"Number of control policy equations must match the action space dimension. Expected {self.action_space.dimension} equations, got {len(self.transitions)}.")
            self.transitions = None
        if not self.transitions:
            self.mode = PolicyMode.SYNTHESIS
            logger.info("No control policy provided. Initializing a default control policy.")
            if not self.prefix:
                logger.error("No prefix provided for the control policy.")
                raise ValueError("No prefix provided for the control policy. You must provide a prefix in synthesis mode.")
            self._initialize_control_policy()
        else:
            self.mode = PolicyMode.VERIFICATION
            self.transitions = [
                Equation.extract_equation_from_string(str(equation))
                for equation in self.transitions
            ]
            logger.info("Control policy provided. Verification mode is enabled.")

    def update_control_policy(self, new_policy: Sequence[Equation]) -> None:
        self.transitions = deepcopy(new_policy)

    def _initialize_control_policy(self) -> None:
        logger.info(f"Initializing a control policy template with a maximal degree of {self.maximal_degree}, for space dimension {self.state_dimension} and action space dimension {self.action_dimension}.")
        _transitions = []
        cp_generator = power_generator(
            poly_max_degree=self.maximal_degree,
            variable_generators=self.state_dimension,
        )
        variable_generators = [f"S{i}" for i in range(1, self.state_dimension + 1)]

        for i in range(1, self.action_dimension+1):
            _pre = f"{self.prefix}_{i}"
            _monomials = [
                Monomial(
                    coefficient=1,
                    variable_generators=variable_generators + [f"{_pre}_{const_postfix}"],
                    power=powers + (1,)
                ) for (const_postfix, powers) in cp_generator
            ]
            _equation = Equation(monomials=_monomials)
            _transitions.append(_equation)

            _new_consts = {f"{_pre}_{const_postfix}" for const_postfix, _ in cp_generator} # TODO: This can be more optimized
            self.generated_constants.update(_new_consts)
        self.transitions = _transitions
        self.constants_founded = True

    def _find_constants(self) -> None:
        for equation in self.transitions:
            for monomial in equation.monomials:
                self.generated_constants.update(monomial.get_symbolic_constant())

    def get_generated_constants(self) -> set[str]:
        if not self.constants_founded:
            self._find_constants()
        return self.generated_constants

    def __str__(self):
        return f"{self.type}: {self.state_dimension} -> {self.action_dimension}"

    def __call__(self) -> Dict[str, Equation]:
        return {
            f"A{i}": equation for i, equation in enumerate(self.transitions, start=1)
        }


@dataclass
class SystemDecomposedControlPolicy:
    action_dimension: int
    state_dimension: int
    maximal_degree: int
    abstraction_dimension: int  # Number of states in the automata (q in LDBA)
    policies: Sequence[SystemControlPolicy] = None
    generated_constants: set[str] = field(init=False, default_factory=set)

    def __post_init__(self):
        self.policies = [
            policy for policy in self.policies if policy
        ]
        if not self.policies:
            self._initialize_synthesized_policies()
        else:
            self._initialize_provided_policies()

        for policy in self.policies:
            self.generated_constants.update(policy.get_generated_constants())

    def _initialize_synthesized_policies(self) -> None:
        logger.info("Initializing control policy for policy synthesis.")
        prefixes = ["Pa"] + [f"Pb{i}" for i in range(self.abstraction_dimension)]
        types = [PolicyType.ACCEPTANCE] + [PolicyType.BUCHI for _ in range(self.abstraction_dimension)]
        self.policies = [
            SystemControlPolicy(
                action_dimension=self.action_dimension,
                state_dimension=self.state_dimension,
                maximal_degree=self.maximal_degree,
                transitions=None,
                prefix=prefix,
                type=ptype
            ) for prefix, ptype in zip(prefixes, types)
        ]

    def get_policy(self, policy_type: PolicyType, policy_id: int = None) -> SystemControlPolicy:
        """Policy id is required for Buchi policies."""
        if policy_type == PolicyType.ACCEPTANCE:
            return self.policies[0]
        if policy_type == PolicyType.BUCHI:
            if policy_id is None:
                raise ValueError("Policy ID is required for Buchi policies.")
            if policy_id >= len(self.policies) - 1 or policy_id < 0:
                raise ValueError(f"Invalid policy ID: {policy_id}.")
            return self.policies[policy_id+1]
        raise ValueError(f"Invalid policy type: {policy_type}.")

    def get_length(self) -> dict[PolicyType, int]:
        return {
            PolicyType.ACCEPTANCE: 1,
            PolicyType.BUCHI: len(self.policies) - 1
        }

    def _initialize_provided_policies(self):
        raise NotImplemented

    def get_generated_constants(self) -> set[str]:
        return self.generated_constants

    def __str__(self):
        return (f"Decomposed control policy: {self.state_dimension} -> {self.action_dimension} (x{len(self.policies)})\n" +
                "\n".join(f"    - {policy}" for policy in self.policies))
