from dataclasses import dataclass, field
from enum import Enum

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
    states: list[AutomataState]
    accepting_sink_sets_id: list[str]
    atomic_symbol_to_propositions: dict[str, int]
    # accepting_sinks_states_id: dict[str, list[str]] = field(init=False, default_factory=dict)

    # def __post_init__(self):
    #     self.accepting_sinks_states_id = {
    #         sink_id: [] for sink_id in self.accepting_sink_sets_id
    #     }
    #     for state in self.states:
    #         if state.is_accepting():
    #             for acc_id in state.accepting_signature:
    #                 self.accepting_sinks_states_id[acc_id].append(state.state_id)

    def __str__(self):
        start = f">> {self.start_state_id}"
        states = "\n".join([str(st) for st in self.states])
        return f"{start}\n{states}"

    @classmethod
    def from_hoa(cls, hoa_header, hoa_states: list[HOAAutomataState]):
        start_state_id = hoa_header['start_state_id']
        accepting_sink_components = hoa_header['accepting_sink_sets_id']
        propositions_translation_dict = hoa_header['atomic_symbol_to_propositions']
        last_state_id = len(hoa_states) - 1
        org_states = []
        synth_states = []

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
                        state_id=last_state_id,
                        status=AutomataStateStat.Accepting,
                        transitions=[epsilon_tr],
                        accepting_signature=tr.accepting_signature
                    )
                    synth_states.append(new_state)

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
            org_states.append(new_st)

        states = org_states + synth_states
        return cls(
            start_state_id=start_state_id,
            states=states,
            accepting_sink_sets_id=accepting_sink_components,
            atomic_symbol_to_propositions=propositions_translation_dict
        )

