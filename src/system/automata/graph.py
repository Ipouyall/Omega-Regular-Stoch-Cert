from dataclasses import dataclass, field
from typing import List

from .sub_graph import AcceptanceStatus, AutomataTransition, AutomataState
from .utils import _fast_dict_replacement
from .algorithm import find_bottom_sccs_covering_accepting_sink_sets

_a_to_z_string = "abcdefghijklmnopqrstuvwxyz"


def convert_to_state_acceptance(states: List[AutomataState]):
    state_count = len(states)
    for st_idx in range(state_count):
        for tr_idx in range(len(states[st_idx].transitions)):
            if states[st_idx].transitions[tr_idx].acc_sig:
                back_tr = AutomataTransition(
                    destination=states[st_idx].state_id,
                    acc_sig=[],
                    label="",
                )
                forward_tr = AutomataTransition(
                    destination=state_count,
                    acc_sig=[],
                    label=states[st_idx].transitions[tr_idx].label,
                )
                new_state = AutomataState(
                    state_id=state_count,
                    acc_sig=states[st_idx].transitions[tr_idx].acc_sig,
                    transitions=[back_tr]
                )
                states[st_idx].transitions[tr_idx] = forward_tr
                states.append(new_state)
                state_count += 1


@dataclass
class Automata:
    start_state_id: str
    states: List[AutomataState]
    accepting_sink_sets_id: list[str]
    symbol_to_atomic_propositions: dict[int, str]
    atomic_preposition_lookup: dict[str, str]
    lookup_table: dict[str, str] = field(init=False, default_factory=dict)

    def __post_init__(self):
        self.start_state_id = str(self.start_state_id)
        self._normalize_graph()
        self.lookup_table = {
            str(k): _fast_dict_replacement(str(v), self.atomic_preposition_lookup)
            for k, v in self.symbol_to_atomic_propositions.items()
        }

    def _normalize_graph(self):
        convert_to_state_acceptance(self.states)
        bottom = find_bottom_sccs_covering_accepting_sink_sets(self.states, self.accepting_sink_sets_id)
        accepting_nodes = {int(node) for component in bottom for node in component}
        for idx in range(len(self.states)):
            is_in_bottom_scc = self.states[idx].state_id in accepting_nodes
            stat = AcceptanceStatus.Accepting if is_in_bottom_scc else AcceptanceStatus.NonAccepting
            self.states[idx].acceptance_status = stat

    def get_state(self, state_id: int):
        return self.states[int(state_id)]

    def to_detailed_string(self):
        start = f"  → {self.start_state_id}"
        sp = " "
        states = ("\n"+sp).join([st.to_string(self.lookup_table) for st in self.states])
        return f"{self}\n{start}\n{sp}{states}"

    def __str__(self):
        return f"Automata(|Q|={len(self.states)}, q0={'{'}{self.start_state_id}{'}'}, |Σ|={len(self.symbol_to_atomic_propositions.keys())}, F={'{'}{','.join(self.accepting_sink_sets_id)}{'}'})"

    @classmethod
    def from_hoa(cls, hoa_header, hoa_states: List[AutomataState], lookup_table: dict):
        propositions_translation_dict = {
            int(i): str(ap)
            for i, ap in enumerate(hoa_header['ap_decl']["propositions"], start=0)
        }

        return cls(
            start_state_id=hoa_header['start_state'],
            states=hoa_states,
            accepting_sink_sets_id=list(map(str, hoa_header['acceptance']['buchi_sets'])),
            symbol_to_atomic_propositions=propositions_translation_dict,
            atomic_preposition_lookup=lookup_table
        )

