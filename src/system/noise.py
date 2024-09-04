from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
import numpy as np


__valid__distributions__ = ["normal"]
__max__expectation__order__ = 10


class NoiseGenerator(ABC):

    @abstractmethod
    def generate_noise(self) -> list[float, ...]:
        pass

    @abstractmethod
    def get_state(self):
        pass

    @abstractmethod
    def get_expectations(self, order) -> list[float]:
        pass

    @abstractmethod
    def __call__(self, *args, **kwargs):
        pass

    @abstractmethod
    def __iter__(self):
        pass

    @abstractmethod
    def __next__(self):
        pass


@dataclass
class NormalNoiseGenerator(NoiseGenerator):  # TODO: later we have to add expectations for each distribution
    """
    A class to generate noise based on the normal distribution, with state preservation.

    Attributes:
        mean (float): Mean of the normal distribution.
        std_dev (float): Standard deviation of the normal distribution.
        dimension (int): Dimension of the noise to generate.
        seed (Optional[int]): Optional seed for reproducibility.
        rng (np.random.Generator): A random number generator instance.
    """
    mean: float
    std_dev: float
    dimension: int
    seed: Optional[int] = None
    rng: np.random.Generator = field(init=False)

    __expectation_table__ = [
        lambda mu, sigma: mu,
        lambda mu, sigma: mu**2 + sigma**2,
        lambda mu, sigma: mu**3 + 3*mu*sigma**2,
        lambda mu, sigma: mu**4 + 6*mu**2*sigma**2 + 3*sigma**4,
        lambda mu, sigma: mu**5 + 10*mu**3*sigma**2 + 15*mu*sigma**4,
        lambda mu, sigma: mu**6 + 15*mu**4*sigma**2 + 45*mu**2*sigma**4 + 15*sigma**6,
        lambda mu, sigma: mu**7 + 21*mu**5*sigma**2 + 105*mu**3*sigma**4 + 105*mu*sigma**6,
        lambda mu, sigma: mu**8 + 28*mu**6*sigma**2 + 210*mu**4*sigma**4 + 420*mu**2*sigma**6 + 105*sigma**8,
        lambda mu, sigma: mu**9 + 36*mu**7*sigma**2 + 378*mu**5*sigma**4 + 1260*mu**3*sigma**6 + 945*mu*sigma**8,
        lambda mu, sigma: mu**10 + 45*mu**8*sigma**2 + 630*mu**6*sigma**4 + 3150*mu**4*sigma**6 + 4725*mu**2*sigma**8 + 945*sigma**10
    ]

    def __post_init__(self):
        """
        Initializes the random number generator after the dataclass has been created.
        """
        self._set_rng()

    def _set_rng(self):
        if self.seed is not None:
            self.rng = np.random.default_rng(self.seed)
        else:
            self.rng = np.random.default_rng()

    def generate_noise(self) -> list[float]:
        """
        Generates a tuple of noise values according to the specified normal distribution.

        Returns:
            Tuple[float, ...]: A tuple containing `dimension` noise values.
        """
        return list(self.rng.normal(self.mean, self.std_dev, self.dimension))

    def get_state(self):
        """
        Returns the current state of the random number generator.
        """
        return self.rng.bit_generator.state

    def get_expectations(self, order) -> list[float]:
        """
        Returns the expected values of the noise distribution.
        """
        return [self.__expectation_table__[i](self.mean, self.std_dev) for i in range(order)]

    def __call__(self, *args, **kwargs):
        return self.generate_noise()

    def __iter__(self):
        self._set_rng()
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
    distribution_generator_parameters: dict
    noise_generators: NoiseGenerator = field(init=False)

    def __post_init__(self):
        if self.distribution_name not in __valid__distributions__:
            raise ValueError(f"Invalid distribution name: {self.distribution_name}. \
            Valid distributions are: {__valid__distributions__}")

        if self.distribution_name == "normal":
            self.noise_generators = NormalNoiseGenerator(dimension=self.dimension, **self.distribution_generator_parameters)

    def get_expectations(self, max_deg) -> list[float]:
        if max_deg > __max__expectation__order__:
            raise ValueError(f"Maximal degree of expectation is {__max__expectation__order__}.")
        return self.noise_generators.get_expectations(max_deg)


    def __call__(self, *args, **kwargs):
        """
        Generates the next set of noise values from the noise generators.

        Returns:
            tuple: A tuple containing the next set of noise values from each generator.
        """
        return next(self.noise_generators)
