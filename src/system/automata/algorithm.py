from typing import List, Dict, Sequence, TypeAlias

from .sub_graph import AutomataState

Graph: TypeAlias = Dict[int, List[int]]

def build_graph(states: List[AutomataState], excluded_state_ids: List[int]) -> Graph:
    return {
        st.state_id: [tr.destination for tr in st.transitions if tr.destination not in excluded_state_ids]
        for st in states if st.state_id not in excluded_state_ids
    }


def build_reverse_graph(states: List[AutomataState]) -> Graph:
    gf = {st.state_id: list() for st in states}
    for st in states:
        for tr in st.transitions:
            gf[tr.destination].append(st.state_id)
    return gf


def tarjan_scc(graph: Graph) -> List[List[int]]:
    index = 0
    indices = {}
    lowlink = {}
    stack = []
    on_stack = set()
    sccs = []

    def strong_connect(v: int):
        nonlocal index
        indices[v] = index
        lowlink[v] = index
        index += 1
        stack.append(v)
        on_stack.add(v)

        for w in graph.get(v, []):
            if w not in indices:
                strong_connect(w)
                lowlink[v] = min(lowlink[v], lowlink[w])
            elif w in on_stack:
                lowlink[v] = min(lowlink[v], indices[w])

        if lowlink[v] == indices[v]:
            scc = []
            while True:
                w = stack.pop()
                on_stack.remove(w)
                scc.append(w)
                if w == v:
                    break
            sccs.append(scc)

    for _v in graph.keys():
        if _v not in indices:
            strong_connect(_v)

    return sccs


def is_bottom_scc(scc: Sequence[int], graph: Graph) -> bool:
    """
    Checks if an SCC is a bottom SCC.
    An SCC is a bottom SCC if none of its nodes have outgoing edges to nodes outside the SCC.
    """
    for node in scc:
        for neighbor in graph.get(node, []):
            if neighbor not in scc:
                return False
    return True


def find_accessible_states_using_bfs(graph: Graph, starting_states: Sequence[int]) -> List[bool]:
    visited_states: List[bool] = [False] * len(graph)
    for state_id in starting_states:
        visited_states[state_id] = True
    queue = list(starting_states)

    while queue:
        current = queue.pop(0)
        for neighbor in graph.get(current, []):
            if not visited_states[neighbor]:
                visited_states[neighbor] = True
                queue.append(neighbor)
    return visited_states


def find_rejecting_states(states: List[AutomataState]) -> List[int]:
    graph = build_reverse_graph(states)
    accepting_states = [st.state_id for st in states if st.is_accepting()]
    is_not_rejecting = find_accessible_states_using_bfs(graph, accepting_states)
    return [idx for idx, not_rejecting in enumerate(is_not_rejecting) if not not_rejecting]


def find_bottom_sccs_covering_accepting_sink_sets(automata_states: List[AutomataState], accepting_component_ids: set[int], rejecting_states: List[int]) -> List[List[str]]:
    graph = build_graph(automata_states, excluded_state_ids=rejecting_states)
    strongly_connected_components = tarjan_scc(graph)
    bottom_strongly_connected_components = []

    for scc in strongly_connected_components:
        if not is_bottom_scc(scc, graph):
            continue
        accepting_signatures = set()
        for state_id in scc:
            state = automata_states[state_id]
            accepting_signatures.update(state.acc_sig)
        if accepting_component_ids.issubset(accepting_signatures):
            bottom_strongly_connected_components.append(scc)
    return [list(map(str, scc)) for scc in bottom_strongly_connected_components]
