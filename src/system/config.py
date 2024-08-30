from dataclasses import dataclass
from typing import List


__valid_theorems__ = ["handelman"]
__valid_solvers__ = ["z3", "mathsat"]


@dataclass
class SynthesisConfig:
    """
    Holds configuration settings for the synthesis process based on API calling of external solvers.
    """
    maximal_polynomial_degree: int
    expected_values: List[float]
    theorem_name: str = "handelman"
    solver_name: str = "z3"
    # TODO: we may need to add more configuration settings here later

    def __post_init__(self):
        if self.maximal_polynomial_degree < 1:
            raise ValueError("The maximum polynomial degree must be greater than or equal to 1.")
        if len(self.expected_values) == 0:
            raise ValueError("The list of expected values for the stochastic disturbance must not be empty.")
        if len(self.expected_values) != self.maximal_polynomial_degree:
            raise ValueError("The number of expected values must match the maximum polynomial degree.")

        if self.theorem_name not in __valid_theorems__:
            raise ValueError(f"Invalid theorem name ({self.theorem_name}). Choose one of {__valid_theorems__}.")

        if self.solver_name not in __valid_solvers__:
            raise ValueError(f"Invalid solver name ({self.solver_name}). Choose one of {__valid_solvers__}.")

