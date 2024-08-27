from dataclasses import dataclass
from typing import Tuple, Generator


@dataclass
class SystemStochasticNoise:
    """
    Represents a system with stochastic noise generators.
    """

    dimension: int
    distribution_name: str
    noise_generators: Generator[None, Tuple[float]]

    # TODO: later in post-init, initialize the noise generators based on the distribution name

    def get_expectations(self, max_deg): pass # TODO: Complete this


    def __call__(self, *args, **kwargs):
        """
        Generates the next set of noise values from the noise generators.

        Returns:
            tuple: A tuple containing the next set of noise values from each generator.
        """
        return next(self.noise_generators)
