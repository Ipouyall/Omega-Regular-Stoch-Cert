from dataclasses import dataclass, field
from enum import Enum
from typing import Dict

from .hoaParser import HOAAutomataState
from .utils import find_bottom_sccs_covering_accepting_sink_sets


_a_to_z_string = "abcdefghijklmnopqrstuvwxyz"

def _rapid_reversed_dict_replacement(string, **kwargs):
    for key, value in kwargs.items():
        string = string.replace(str(value), str(key))
    return string

def _rapid_dict_replacement(string, **kwargs):
    keep_alive = 1
    while keep_alive != 0:
        keep_alive = 0
        for key, value in kwargs.items():
            _string = string.replace(str(key), str(value))
            keep_alive += 1 if _string != string else 0
            string = _string
    return string

def _fast_dict_replacement(string, lookup: dict, safe=False):
    for key in lookup.keys():
        string = string.replace(str(key), f"'''{key}'''")
    for key, value in lookup.items():
        _v = f"({value})" if safe else str(value)
        string = string.replace(f"'''{key}'''", _v)
    return string

class AutomataTransitionType(Enum):
    Epsilon = "epsilon"
    Propositional = "propositional"

    @classmethod
    def from_str(cls, value: str):
        value = value.strip()
        if value in ["epsilon", "e", "any", "t"] or len(value) == 0:
            return cls.Epsilon
        return cls.Propositional

    def to_string(self):
        return "ε" if self != AutomataTransitionType.Propositional else self.value


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
        if self.type == AutomataTransitionType.Epsilon:
            self.predicate = ""
        self.predicate = self.predicate.replace("&", " & ").replace("|", " | ")

    def to_string(self, lookup_table):
        _pred = _fast_dict_replacement(self.predicate, lookup_table, safe=True)
        return f"--[{_pred:^10}]--> {self.destination_id}"

    def __str__(self):
        return self.to_string({})


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

    def to_string(self, lookup_table):
        t = "\n" + 11 * " "
        # acc_sig = f"{'{'+','.join(self.accepting_signature)+'}'}" if self.accepting_signature else " "
        return f"  - {self.status} {self.state_id:<3}" + t.join([tr.to_string(lookup_table) for tr in self.transitions])

    def __str__(self):
        return self.to_string({})


@dataclass
class Automata:
    start_state_id: str
    states: Dict[str, AutomataState]
    accepting_sink_sets_id: list[str]
    symbol_to_atomic_propositions: dict[int, str]
    atomic_preposition_lookup: dict[str, str]
    lookup_table: dict[str, str] = field(init=False, default_factory=dict)


    def __post_init__(self):
        # self._fix_transitions_labels()
        self._discover_accepting_components()
        self.lookup_table = {
            str(k): _fast_dict_replacement(str(v), self.atomic_preposition_lookup)
            for k, v in self.symbol_to_atomic_propositions.items()
        }

    def _fix_transitions_labels(self):
        for state in self.states.values():
            for tr in state.transitions:
                tr.predicate = _rapid_reversed_dict_replacement(tr.predicate, **self.symbol_to_atomic_propositions)

    def _discover_accepting_components(self):
        self.accepting_components = find_bottom_sccs_covering_accepting_sink_sets(self)
        accepting_nodes = {node for component in self.accepting_components for node in component}
        for node in accepting_nodes:
            self.states[node].status = AutomataStateStat.Accepting

    def get_state(self, state_id: str):
        return self.states[state_id]

    def to_detailed_string(self):
        start = f"  → {self.start_state_id}"
        states = "\n".join([st.to_string(self.lookup_table) for st in self.states.values()])
        return f"{self}\n{start}\n{states}"

    def __str__(self):
        return f"Automata(|Q|={len(self.states)}, q0={'{'}{self.start_state_id}{'}'}, |Σ|={len(self.symbol_to_atomic_propositions.keys())}, F={'{'}{','.join(self.accepting_sink_sets_id)}{'}'})"

    @classmethod
    def from_hoa(cls, hoa_header, hoa_states: list[HOAAutomataState], lookup_table: dict):
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
                        type=AutomataTransitionType.from_str(tr.label),
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
            symbol_to_atomic_propositions=propositions_translation_dict,
            atomic_preposition_lookup=lookup_table
        )

