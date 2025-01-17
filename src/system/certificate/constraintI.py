from abc import ABC, abstractmethod

from .constraint import ConstraintInequality


class Constraint(ABC):
    @abstractmethod
    def extract(self) -> list[ConstraintInequality]:
        pass
