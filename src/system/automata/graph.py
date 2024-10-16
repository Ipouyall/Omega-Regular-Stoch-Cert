from dataclasses import dataclass, field
from enum import Enum
from typing import Dict

from .hoaParser import HOAAutomataState


class AutomataTransitionType(Enum):
    Any = "any"
    Epsilon = "epsilon"
    Propositional = "propositional"

    @classmethod
    def from_str(cls, value: str):
        if value in ["any", "t"]:
            return cls.Any
        if value in ["epsilon", "e"] or len(value) == 0:
            return cls.Epsilon
        return cls.Propositional


class AutomataStateStat(Enum):
    Accepting = "accepting"
    NonAccepting = "non-accepting"

    def __str__(self):
        if self == AutomataStateStat.Accepting:
            return "(●)"
        return "( )"

    @classmethod
    def from_str(cls, value: str):
        if value in ["accepting"]:
            return cls.Accepting
        return cls.NonAccepting


@dataclass
class AutomataTransition:
    type: AutomataTransitionType
    destination_id: str
    predicate: str

    def __post_init__(self):
        self.predicate = self.predicate.replace("&", " & ").replace("|", " | ")

    def __str__(self):
        return f"--[{self.predicate:^5}]--> {self.destination_id}"


@dataclass
class AutomataState:
    state_id: str
    status: AutomataStateStat
    transitions: list[AutomataTransition]
    accepting_signature: list[str]

    def __post_init__(self):
        if not isinstance(self.state_id, str):
            raise ValueError("State ID must be a string.")
        for _as in self.accepting_signature:
            if not isinstance(_as, str):
                raise ValueError("Accepting signature must be a string.")
        if self.status == AutomataStateStat.Accepting and len(self.accepting_signature) == 0:
            raise ValueError("Accepting state must have an accepting signature.")
        if self.status == AutomataStateStat.NonAccepting and len(self.accepting_signature) > 0:
            raise ValueError("Non-accepting state cannot have an accepting signature.")

    def is_accepting(self):
        return self.status == AutomataStateStat.Accepting

    def __str__(self):
        t = "\n" + 9 * " "
        return f"- {self.status} {self.state_id:<3}" + t.join([str(tr) for tr in self.transitions])


@dataclass
class Automata:
    start_state_id: str
    states: Dict[str, AutomataState]
    accepting_sink_sets_id: list[str]
    atomic_symbol_to_propositions: dict[str, int]
    # accepting_states_id: set[str] = field(init=False, default_factory=set)
    #
    # def __post_init__(self):
    #     self.accepting_states_id = {st.state_id for st in self.states.values() if st.is_accepting()}

    def get_state(self, state_id: str):
        return self.states[state_id]

    def to_detailed_str(self):
        start = f">> {self.start_state_id}"
        states = "\n".join([str(st) for st in self.states])
        return f"{start}\n{states}"

    def __str__(self):
        return f"Automata(|Q|={len(self.states)}, q0={'{'}{self.start_state_id}{'}'}, Σ={'{'}{','.join(self.atomic_symbol_to_propositions.keys())}{'}'}, F={'{'}{','.join(self.accepting_sink_sets_id)}{'}'})"

    @classmethod
    def from_hoa(cls, hoa_header, hoa_states: list[HOAAutomataState]):
        start_state_id = hoa_header['start_state_id']
        accepting_sink_components = hoa_header['accepting_sink_sets_id']
        propositions_translation_dict = hoa_header['atomic_symbol_to_propositions']
        last_state_id = len(hoa_states) - 1
        refined_states: Dict[str, AutomataState] = {}

        for state in hoa_states:
            trans = []
            for tr in state.transitions:
                if tr.accepting_signature:
                    last_state_id += 1
                    epsilon_tr = AutomataTransition(
                        type=AutomataTransitionType.Epsilon,
                        destination_id=tr.destination,
                        predicate=""
                    )
                    new_state = AutomataState(
                        state_id=str(last_state_id),
                        status=AutomataStateStat.Accepting,
                        transitions=[epsilon_tr],
                        accepting_signature=tr.accepting_signature
                    )
                    refined_states[new_state.state_id] = new_state


                    new_tr = AutomataTransition(
                        type=AutomataTransitionType.Propositional,
                        destination_id=last_state_id,
                        predicate=tr.label
                    )
                else:
                    new_tr = AutomataTransition(
                        type=AutomataTransitionType.from_str(tr.label),
                        destination_id=tr.destination,
                        predicate=tr.label,
                    )
                trans.append(new_tr)
            new_st = AutomataState(
                state_id=state.state_id,
                status=AutomataStateStat.NonAccepting,
                transitions=trans,
                accepting_signature=[]
            )
            refined_states[new_st.state_id] = new_st

        return cls(
            start_state_id=start_state_id,
            states=refined_states,
            accepting_sink_sets_id=accepting_sink_components,
            atomic_symbol_to_propositions=propositions_translation_dict
        )

