from itertools import product
from functools import lru_cache
from typing import Union


@lru_cache(maxsize=4)
def power_generator(poly_max_degree: int, variable_generators: Union[tuple[str], int]):
    """
    The output is designed as a list of tuples (constant, powers) where the constant is a string and the powers is a tuple of integers, corresponding to the powers of the variables in the polynomial, with the same order as the input.
    """
    if isinstance(variable_generators, int):
        len_v = variable_generators
    else:
        len_v = len(variable_generators)

    power_combinations = product(range(poly_max_degree + 1), repeat=len_v)
    power_combinations = (powers for powers in power_combinations if sum(powers) <= poly_max_degree)

    return tuple(
        (str(i), powers)
        for i, powers in enumerate(power_combinations, start=1)
    )
