from dataclasses import dataclass
from typing import List


@dataclass
class Space:  # TODO: complete this
    dimension: int # TODO: are dimensions needed?
    inequalities: List[str]
