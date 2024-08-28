from dataclasses import dataclass
from typing import List, Union, Dict
from numbers import Number

from src.system import logger


@dataclass
class SystemState:
    """
    Represents a set of states defined by inequalities.

    Attributes:
        state_values (List[Number]):
            A list of numerical values representing the state.
        dimension (Union[int, None]):
            The dimension of the state space. If None, it will be inferred from the length of state_values.
    """
    state_values: List[Number]
    dimension: Union[int, None] = None

    def __post_init__(self):
        """
        Post-initialization processing to set the dimension if not provided and ensure consistency
        between the number of state values and the dimension.

        Raises:
            ValueError: If the dimension is set to 0.
        """
        if self.dimension is None:
            logger.warning("The dimension of the state space has not been set. Attempting to infer the dimension from the number of state values.")
            self.dimension = len(self.state_values)
        if len(self.state_values) != self.dimension:
            logger.warning(f"The number of state values does not match the dimension of the state space \
            ({len(self.state_values)} != {self.dimension}). Correcting the dimension based on the number of state values.")

        if self.dimension == 0:
            raise ValueError("The dimension of the state space must be greater than 0.")

    def __call__(self, *args, **kwargs):
        """
        Returns the state values as a tuple.
        """
        return tuple(self.state_values)

    def __str__(self):
        """
        Returns a string representation of the State object.

        Returns:
            str: A string representing the state values.
        """
        return f"State: {self.state_values}"

