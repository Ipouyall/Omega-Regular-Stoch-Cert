from typing import Dict, List, Sequence


def build_graph(automata: "Automata") -> Dict[int, List[int]]:
    graph = {}
    for state_id, state in automata.states.items():
        destinations = []
        for transition in state.transitions:
            destinations.append(int(transition.destination_id))
        graph[int(state_id)] = destinations
    return graph

def tarjan_scc(graph: Dict[int, List[int]]) -> List[List[int]]:
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

def is_bottom_scc(scc: Sequence[int], graph: Dict[int, List[int]]) -> bool:
    """
    Checks if an SCC is a bottom SCC.
    An SCC is a bottom SCC if none of its nodes have outgoing edges to nodes outside the SCC.
    """
    for node in scc:
        for neighbor in graph.get(node, []):
            if neighbor not in scc:
                return False
    return True

def find_bottom_sccs_covering_accepting_sink_sets(automata: "Automata") -> List[List[str]]:
    graph = build_graph(automata)
    sccs = tarjan_scc(graph)
    accepting_sink_sets_id_set = set(automata.accepting_sink_sets_id)
    result_sccs = []

    for scc in sccs:
        if not is_bottom_scc(scc, graph):
            continue
        accepting_signatures = set()
        for state_id in scc:
            state = automata.get_state(str(state_id))
            accepting_signatures.update(state.accepting_signature)
        if accepting_sink_sets_id_set.issubset(accepting_signatures):
            result_sccs.append(scc)
    return [list(map(str, scc)) for scc in result_sccs]