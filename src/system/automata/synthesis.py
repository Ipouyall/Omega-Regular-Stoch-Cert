import os.path
from dataclasses import dataclass, field
from typing import Optional

from . import logger
from .owlUtil import execute_ltl2ldba_tool


@dataclass
class PredicateLookup:
    """
    A class to store the predicate lookup table.

    Attributes:
        lookup_table (dict): A dictionary that maps predicate names to their corresponding inequality.
    """
    lookup_table: dict

    __slots__ = ["lookup_table"]

    def __post_init__(self):
        """Check the type of the attributes and log or raise an error if the types don't match."""
        if not isinstance(self.lookup_table, dict):
            raise TypeError(
                f"Attribute 'lookup_table' is expected to be of type dict, but got {type(self.lookup_table)} instead."
            )


@dataclass
class LDBASpecification:
    """
    A class to store the specification of the system.

    Attributes:
        ltl_formula (str): A string representing the LTL formula.
        predicate_lookup (PredicateLookup): A lookup table for predicates.
        owl_binary_path (str): The path to the OWL binary file.
        hoa_path (str): The HOA representation of the LTL formula (optional).
    """
    ltl_formula: str
    predicate_lookup: PredicateLookup
    owl_binary_path: str
    hoa_path: Optional[str] = None
    hoa: str = field(init=False, default=None)

    def __post_init__(self):
        if not isinstance(self.predicate_lookup, PredicateLookup) and isinstance(self.predicate_lookup, dict):
            self.predicate_lookup = PredicateLookup(self.predicate_lookup)
        elif not isinstance(self.predicate_lookup, PredicateLookup):
            raise TypeError(
                f"Attribute 'predicate_lookup' is expected to be of type PredicateLookup, but got {type(self.predicate_lookup)} instead."
            )
        if not os.path.exists(self.owl_binary_path) and not self.hoa:
            raise FileNotFoundError(f"OWL binary file not found at path: {self.owl_binary_path}")
        if self.hoa_path:
            with open(self.hoa_path, "r") as f:
                self.hoa = f.read().strip()
            logger.warning("HOA path is already provided. Later, the HOA generation will be skipped.")
        elif not self.ltl_formula:
            raise ValueError("At least one of the 'ltl_formula' or 'hoa_path' attributes must be provided.")


    def get_HOA(self, output_path):
        if self.hoa is None:
            logger.info("Generating HOA representation of the LTL formula.")
            self.hoa = execute_ltl2ldba_tool(self.owl_binary_path, self.ltl_formula)
            with open(output_path, "w") as f:
                f.write(self.hoa)
            return self.hoa
        return self.hoa
