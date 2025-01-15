from abc import ABC, abstractmethod
import re

from .constraint import ConstraintInequality


class Constraint(ABC):
    @abstractmethod
    def extract(self) -> list[ConstraintInequality]:
        pass


def _replace_keys_with_values(s, dictionary):
    pattern = re.compile("|".join(re.escape(key) for key in dictionary.keys()))
    result = pattern.sub(lambda match: dictionary[match.group(0)], s)
    return result
