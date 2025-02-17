from abc import ABC, abstractmethod

from .constraint import ConstraintImplication


class Constraint(ABC):
    @abstractmethod
    def extract(self) -> list[ConstraintImplication]:
        pass
