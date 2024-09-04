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
    theorem_name: str
    solver_name: str

    __slots__ = ["maximal_polynomial_degree", "expected_values", "theorem_name", "solver_name"]
    # TODO: we may need to add more configuration settings here later

    def __post_init__(self):
        if self.maximal_polynomial_degree < 1:
            raise ValueError("The maximum polynomial degree must be greater than or equal to 1.")

        if self.theorem_name not in __valid_theorems__:
            raise ValueError(f"Invalid theorem name ({self.theorem_name}). Choose one of {__valid_theorems__}.")

        if self.solver_name not in __valid_solvers__:
            raise ValueError(f"Invalid solver name ({self.solver_name}). Choose one of {__valid_solvers__}.")

