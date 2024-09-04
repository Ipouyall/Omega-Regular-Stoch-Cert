from dataclasses import dataclass


@dataclass
class Space:
    """
    Each inequality defines boundaries one of the dimensions of the state space.
    """
    dimension: int
    inequalities: str # TODO: fix this later

    __slots__ = ["dimension", "inequalities"]

    def __post_init__(self):
        if not isinstance(self.inequalities, str):
            raise TypeError("inequalities must be a string")
        if self.dimension <= 0:
            raise ValueError("dimension must be a positive integer")
        # if len(self.inequalities) != self.dimension:
        #     raise ValueError("You must provide boundaries for all dimensions")

    def get_inequalities(self):
        return self.inequalities
