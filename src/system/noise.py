from abc import ABC, abstractmethod
from dataclasses import dataclass, field

__valid__distributions__ = ["normal", "uniform"]


class NoiseGenerator(ABC):
    @abstractmethod
    def get_expectations(self, order) -> dict[str, str]:
        pass

    @abstractmethod
    def get_bounds(self) -> dict[str, dict[str, str]]:
        pass


@dataclass
class NormalNoiseGenerator(NoiseGenerator):
    """
    A class to generate noise based on the normal distribution, with state preservation.

    Attributes:
        mean (float): Mean of the normal distribution.
        std_dev (float): Standard deviation of the normal distribution.
        dimension (int): Dimension of the noise to generate.
    """
    mean: list[float]
    std_dev: list[float]
    dimension: int

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
        if len(self.mean) != self.dimension:
            raise ValueError(f"Dimension of mean vector ({len(self.mean)}) does not match the specified dimension ({self.dimension}).")
        if len(self.std_dev) != self.dimension:
            raise ValueError(f"Dimension of standard deviation vector ({len(self.std_dev)}) does not match the specified dimension ({self.dimension}).")

    def get_expectations(self, order=10) -> dict[str, str]:
        """
        Returns the expected values of the noise distribution.
        """
        if order > 10:
            raise ValueError("Expectations higher than order 10 are not supported for the normal distribution.")

        _exp = [
            [self.__expectation_table__[i](self.mean[j], self.std_dev[j])
            for i in range(order)]
            for j in range(self.dimension)
        ]
        refined_disturbance_expectations = {
            f"D{dim + 1}**{i}": str(d)
            for dim in range(len(_exp))
            for i, d in enumerate(_exp[dim], start=1)
        }
        for dim in range(len(_exp)):
            refined_disturbance_expectations[f"D{dim + 1}"] = str(_exp[dim][0])
        return refined_disturbance_expectations

    def get_bounds(self) -> dict[str, dict[str, str]]:
        return {}


@dataclass
class UniformNoiseGenerator(NoiseGenerator):
    """
    A class to generate noise based on the uniform distribution, with state preservation.

    Attributes:
        lower_bound (list[float]): Lower bounds of the uniform distribution for each dimension.
        upper_bound (list[float]): Upper bounds of the uniform distribution for each dimension.
        dimension (int): Dimension of the noise to generate.
    """
    lower_bound: list[float]
    upper_bound: list[float]
    dimension: int

    def __post_init__(self):
        """
        Validates the bounds and initializes the random number generator after the dataclass has been created.
        """
        if len(self.lower_bound) != self.dimension:
            raise ValueError(
                f"Dimension of lower_bound vector ({len(self.lower_bound)}) does not match the specified dimension ({self.dimension}).")
        if len(self.upper_bound) != self.dimension:
            raise ValueError(
                f"Dimension of upper_bound vector ({len(self.upper_bound)}) does not match the specified dimension ({self.dimension}).")
        if any(lb >= ub for lb, ub in zip(self.lower_bound, self.upper_bound)):
            raise ValueError("Each lower bound must be less than the corresponding upper bound.")

    def get_expectations(self, order=2) -> dict[str, str]:
        """
        Returns the expected values of the noise distribution for the uniform distribution.

        Args:
            order (int): The highest order of expectations to compute (currently supports up to order 2).

        Returns:
            dict[str, str]: A dictionary containing the expectations for each dimension.
        """
        if order > 2:
            raise ValueError("Expectations higher than order 2 are not supported for the uniform distribution.")

        expectations = {}
        for dim in range(self.dimension):
            a = self.lower_bound[dim]
            b = self.upper_bound[dim]

            mean = (a + b) / 2
            expectations[f"D{dim + 1}"] = str(mean)
            expectations[f"D{dim + 1}**1"] = str(mean)

            if order >= 2:
                # Second moment (2nd-order expectation)
                second_moment = (a ** 2 + a * b + b ** 2) / 3
                expectations[f"D{dim + 1}**2"] = str(second_moment)

        return expectations

    def get_bounds(self) -> dict[str, dict[str, str]]:
        """
        Returns the bounds of the uniform distribution for each dimension.

        Returns:
            dict[str, dict[str, str]]: A dictionary containing the bounds for each dimension.
        """
        return {
            f"D{dim + 1}": {
                "min": str(self.lower_bound[dim]),
                "max": str(self.upper_bound[dim])
            }
            for dim in range(self.dimension)
        }


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
        elif self.distribution_name == "uniform":
            self.noise_generators = UniformNoiseGenerator(dimension=self.dimension, **self.distribution_generator_parameters)

    def get_expectations(self, max_deg=2) -> dict[str, str]:
        return self.noise_generators.get_expectations(max_deg)

    def get_bounds(self) -> dict[str, dict[str, str]]:
        return self.noise_generators.get_bounds()
