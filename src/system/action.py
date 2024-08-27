from dataclasses import dataclass
from typing import List

from src.system import Space
from src.system.equation import Equation


@dataclass
class SystemActionSpace:
    action_space: Space
    equations: List[Equation]

    # TODO: add "action validation" and "next action" methods

