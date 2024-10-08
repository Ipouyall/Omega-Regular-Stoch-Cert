from itertools import product


def polynomial_generator(poly_max_degree: int, variable_generators: list[str], constants_signature_start: str):
    """
    The output is designed as a list of tuples (constant, powers) where the constant is a string and the powers is a tuple of integers, corresponding to the powers of the variables in the polynomial, with the same order as the input.
    """

    # polynomial with max_degree X means that the sum of each variable's power in a monomial is less than or equal to X
    power_combinations = product(range(poly_max_degree + 1), repeat=len(variable_generators))
    power_combinations = (powers for powers in power_combinations if sum(powers) <= poly_max_degree)

    return (
        (f"{constants_signature_start}_{i}", powers)
        for i, powers in enumerate(power_combinations, start=1)
    )
