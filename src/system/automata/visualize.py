from graphviz import Digraph

from .graph import Automata
from .sub_graph import AcceptanceStatus, AutomataTransitionType


def visualize_automata(automata: Automata, output_file: str = None):
    dot = Digraph(format="png")
    dot.attr(rankdir="LR")

    for st in automata.states:
        state_id = str(st.state_id)
        acc_sig = ""
        if st.acc_sig:
            acc_sig = "\n{" + ", ".join(map(str, st.acc_sig)) + "}"
        shape = "doublecircle" if st.acc_sig else "circle"
        dot.node(
            state_id,
            label=state_id + acc_sig,
            shape=shape,
            style="filled",
            fillcolor="lightblue" if st.acceptance_status.value == AcceptanceStatus.Accepting.value else "#FF6666" if st.acceptance_status.value == AcceptanceStatus.Rejecting.value else "white"
        )

    for st in automata.states:
        state_id = str(st.state_id)
        for idx, transition in enumerate(st.transitions):
            destination_id_str = str(transition.destination)
            label = (
                transition.to_label_string(automata.lookup_table) if transition.type.value == AutomataTransitionType.Propositional.value
                else "ε"
            )
            dot.edge(
                state_id,
                destination_id_str,
                label=label,
            )

    start_state_id = automata.start_state_id
    dot.node("start", shape="point", color="black")
    dot.edge("start", start_state_id)

    if output_file:
        dot.render(output_file, cleanup=True)
    return dot