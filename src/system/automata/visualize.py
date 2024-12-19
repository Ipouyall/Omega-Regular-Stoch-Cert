from graphviz import Digraph

from .graph import AutomataTransitionType, AutomataStateStat, Automata


def visualize_automata(automata: Automata, output_file: str = None):
    dot = Digraph(format="png")
    dot.attr(rankdir="LR")

    for state_id, state in automata.states.items():
        state_id = str(state_id)
        shape = "doublecircle" if state.status == AutomataStateStat.Accepting else "circle"
        dot.node(
            state_id,
            label=state_id,
            shape=shape,
            style="filled",
            fillcolor="lightblue" if state.status == AutomataStateStat.Accepting else "white"
        )

    for state_id, state in automata.states.items():
        state_id = str(state_id)
        for idx, transition in enumerate(state.transitions):
            destination_id_str = str(transition.destination_id)
            label = (
                transition.predicate if transition.type == AutomataTransitionType.Propositional
                else transition.type.to_string()
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