from dataclasses import dataclass, field
from typing import Tuple, Generator, Optional
import numpy as np


@dataclass
class NormalNoiseGenerator:
    """
    A class to generate noise based on the normal distribution, with state preservation.

    Attributes:
        mean (float): Mean of the normal distribution.
        std_dev (float): Standard deviation of the normal distribution.
        dimension (int): Dimension of the noise to generate.
        seed (Optional[int]): Optional seed for reproducibility.
        rng (np.random.Generator): A random number generator instance.
    """
    mean: float = 0.0
    std_dev: float = 1.0
    dimension: int = 1
    seed: Optional[int] = None
    rng: np.random.Generator = field(init=False)

    def __post_init__(self):
        """
        Initializes the random number generator after the dataclass has been created.
        """
        self.rng = np.random.default_rng()

    def generate_noise(self) -> Tuple[float, ...]:
        """
        Generates a tuple of noise values according to the specified normal distribution.

        Returns:
            Tuple[float, ...]: A tuple containing `dimension` noise values.
        """
        return tuple(self.rng.normal(self.mean, self.std_dev, self.dimension))

    def get_state(self):
        """
        Returns the current state of the random number generator.
        """
        return self.rng.bit_generator.state

    def __call__(self, *args, **kwargs):
        return self.generate_noise()

    def __iter__(self):
        return self

    def __next__(self):
        return self.generate_noise()


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
