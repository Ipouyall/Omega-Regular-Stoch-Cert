from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Union

from .utils import _fast_dict_replacement


class AcceptanceStatus(Enum):
    Accepting = "accepting"
    NonAccepting = "non-accepting"
    Rejecting = "rejecting"

    def __str__(self):
        if self == AcceptanceStatus.Accepting:
            return "(●)"
        if self == AcceptanceStatus.Rejecting:
            return "(✗)"
        return "( )"

    @classmethod
    def from_str(cls, value: str):
        if value in ["accepting", "acc"]:
            return cls.Accepting
        if value in ["rejecting", "rej"]:
            return cls.Rejecting
        return cls.NonAccepting


class AutomataTransitionType(Enum):
    Epsilon = "epsilon"
    Propositional = "propositional"

    @classmethod
    def from_label(cls, from_label: str) -> "AutomataTransitionType":
        value = from_label.strip()
        if value in ["epsilon", "e", "any", "t", True, ""] or len(value) == 0:
            return cls.Epsilon
        return cls.Propositional

    def to_string(self, label):
        return "ε" if self != AutomataTransitionType.Propositional else label


@dataclass
class AutomataTransition:
    destination: int
    acc_sig: List[int] = field(default_factory=list)
    label: Optional[str] = ""
    acceptance_status: AcceptanceStatus = field(init=False, default=AcceptanceStatus.NonAccepting)
    type: AutomataTransitionType = field(init=False, default=AutomataTransitionType.Propositional)

    def __post_init__(self):
        self.acceptance_status = AcceptanceStatus.Accepting if self.acc_sig else AcceptanceStatus.NonAccepting
        self.type = AutomataTransitionType.from_label(self.label)
        if self.type == AutomataTransitionType.Epsilon:
            self.label = ""

    def to_label_string(self, lookup_table) -> str:
        return _fast_dict_replacement(self.label, lookup_table, safe=True)

    def to_string(self, lookup_table) -> str:
        _label = self.to_label_string(lookup_table)
        return f"[{self.type.to_string(_label)}] -> {self.destination}" + (" {" + ",".join(map(str, self.acc_sig)) + "}" if self.acc_sig else "")

    def __str__(self):
        return self.to_string({})


@dataclass
class AutomataState:
    state_id: int
    acc_sig: List[int] = field(default_factory=list)
    transitions: List[AutomataTransition] = field(default_factory=list)
    label: Optional[str] = ""
    docString: Optional[str] = ""
    acceptance_status: AcceptanceStatus = field(init=False, default=AcceptanceStatus.NonAccepting)

    def __post_init__(self):
        self.acceptance_status = AcceptanceStatus.Accepting if self.acc_sig else AcceptanceStatus.NonAccepting

    def is_accepting(self) -> bool:
        """Whether the state is in accepting component"""
        return self.acceptance_status.value == AcceptanceStatus.Accepting.value

    def is_rejecting(self) -> bool:
        """Whether the state is in rejecting component"""
        return self.acceptance_status.value == AcceptanceStatus.Rejecting.value

    def is_in_accepting_signature(self, acc_sig: Union[int,str,None]) -> bool:
        """To check whether the state is in a accepting signature by asking for signature or has any accepting signature by providing None as the argument"""
        if acc_sig is None:
            return len(self.acc_sig) > 0
        return int(acc_sig) in self.acc_sig

    def to_string(self, lookup_table) -> str:
        parts = [" ", "-", str(self.acceptance_status), f"{self.state_id:^3}"]
        if self.label:
            parts.append(f" ({self.label})")
        if self.docString:
            parts.append(f' "{self.docString}"')
        if self.acc_sig:
            acc_str = ",".join(map(str, self.acc_sig))
            parts.append(f" {{{acc_str}}}")
        header_str = "".join(parts)
        sp = "\n\t  "
        transitions_str_list = [sp + tr.to_string(lookup_table) for tr in self.transitions]
        return header_str + "".join(transitions_str_list)

    def __str__(self):
        return self.to_string({})
