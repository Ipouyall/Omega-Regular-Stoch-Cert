from typing import Dict, Any, List
from lark import Lark, Transformer, Token

from .sub_graph import AutomataState, AutomataTransition


hoa_grammar = r"""
    start: header "--BODY--" body "--END--"

    header: header_item*
    header_item: version
               | properties
               | state_count
               | start_state
               | atomic_prepositions
               | acceptance
               | tool
               | name
               | owl_args
               | acc_name

    version: "HOA:" /v\d+/
    tool: "tool:" ESCAPED_STRING+
    name: "name:" ESCAPED_STRING
    owl_args: "owlArgs:" ESCAPED_STRING+
    start_state: "Start:" INT
    acc_name: "acc-name:" ("generalized-Buchi" INT | "Buchi")
    acceptance: "Acceptance:" INT acceptance_cond*
    properties: ("properties:" PROPERTY+)+
    atomic_prepositions: "AP:" INT (ESCAPED_STRING)*
    state_count: "States:" INT

    acceptance_cond: "Inf(" INT ")" ("&" "Inf(" INT ")")*

    body: state_chunk*
    state_chunk: state_name edge*
    state_name: "State:" label? INT ESCAPED_STRING? acc_sig?
    edge: label? INT acc_sig?
    label: "[" label_expr "]"
    label_expr: boolean
              | INT
              | LOGIC_NOT label_expr
              | L_PAR label_expr R_PAR
              | label_expr LOGIC_OP label_expr
    boolean: BOOLEAN_TRUE | BOOLEAN_FALSE
    acc_sig: "{" INT* "}"


    IDENTIFIER: /[a-zA-Z_][0-9a-zA-Z_-]*/
    STRING: /[a-zA-Z_-]+/
    PROPERTY: "state-labels" | "trans-labels" | "implicit-labels" | "explicit-labels"
             | "state-acc" | "trans-acc" | "univ-branch" | "no-univ-branch"
             | "deterministic" | "complete" | "unambiguous" | "stutter-invariant"
             | "weak" | "very-weak" | "inherently-weak" | "terminal" | "tight"
             | "colored"
    LOGIC_OP: "&" | "|"
    LOGIC_NOT: "!"
    BOOLEAN_TRUE: "true" | "t"
    BOOLEAN_FALSE: "false" | "f"
    L_PAR: "("
    R_PAR: ")"

    %import common.ESCAPED_STRING
    %import common.INT
    %import common.WS
    %ignore WS
"""


class HOA_Transformer(Transformer):
    def start(self, items):
        return {
            'header': items[0],
            'body': items[1]
        }

    def header_item(self, items):
        return items[0]

    def header(self, items):
        result = {
            'version': None,
            'tool': None,
            'name': None,
            'owl_args': None,
            'start_state': None,
            'acc_name': None,
            'acceptance': None,
            'properties': None,
            'ap_decl': None,
            'state_count': None
        }
        for subdict in items:
            for key, val in subdict.items():
                result[key] = val
        return result

    def version(self, items):
        return {'version': items[0].value}

    def tool(self, items):
        vals = [s.strip('"') for s in items]
        return {'tool': vals}

    def name(self, items):
        return {'name': items[0].strip('"')}

    def owl_args(self, items):
        vals = [s.strip('"') for s in items]
        return {'owl_args': vals}

    def start_state(self, items):
        return {'start_state': int(items[0].value)}

    def acc_name(self, items):
        return {'acc_name': " ".join(str(i.value if isinstance(i, Token) else i) for i in items)}

    def acceptance(self, items):
        acc_count = int(items[0].value)
        conds = list()
        for c in items[1:]:
            conds.extend(c)
        return {'acceptance': {"buchi_count": acc_count, "buchi_sets": conds}}

    def properties(self, items):
        return {'properties': [p.value for p in items]}

    def atomic_prepositions(self, items):
        count = int(items[0].value)
        props = [it.value.strip('"') for it in items[1:]]
        return {'ap_decl': {'count': count, 'propositions': props}}

    def state_count(self, items):
        return {'state_count': int(items[0])}

    def acceptance_cond(self, items):
        return [int(i) for i in items]

    def body(self, items):
        return {'states': items}

    def state_chunk(self, items):
        state_info = items[0]
        edges = items[1:]
        return {
            'state': state_info,
            'edges': edges
        }

    def state_name(self, items):
        idx = 0
        label_ = None
        if isinstance(items[idx], dict) and 'label' in items[idx]:
            label_ = items[idx]['label']
            idx += 1
        state_id = int(items[idx].value)
        idx += 1
        name_ = None
        if idx < len(items) and isinstance(items[idx], Token) and items[idx].type == 'ESCAPED_STRING':
            name_ = items[idx].value.strip('"')
            idx += 1
        acc_sig_ = None
        if idx < len(items) and isinstance(items[idx], dict) and 'acc_sig' in items[idx]:
            acc_sig_ = items[idx]['acc_sig']
            idx += 1

        return {
            'label': label_,
            'state_id': state_id,
            'dstring': name_,
            'acc_sig': acc_sig_
        }

    def edge(self, items):
        idx = 0
        label_ = None
        if isinstance(items[idx], dict) and 'label' in items[idx]:
            label_ = items[idx]['label']
            idx += 1

        dest_state = int(items[idx].value)
        idx += 1

        acc_sig_ = None
        if idx < len(items) and isinstance(items[idx], dict) and 'acc_sig' in items[idx]:
            acc_sig_ = items[idx]['acc_sig']

        return {
            'label': label_,
            'destination': dest_state,
            'acc_sig': acc_sig_
        }

    def label(self, items):
        return {'label': items[0]}

    def acc_sig(self, items):
        return {'acc_sig': [int(t.value) for t in items]}

    def label_expr(self, items):
        if len(items) == 1:
            it = items[0]
            return str(it.value if isinstance(it, Token) else it)
        if len(items) == 2:
            op, subexpr = items
            if isinstance(op, Token) and op.type == "LOGIC_NOT":
                return f"!{subexpr}"
            else:
                raise ValueError(f"Unexpected 2-item label_expr: {op=}, {subexpr=}")
        if len(items) == 3:
            a, op, b = items
            if isinstance(op, Token) and op.type == "LOGIC_OP":
                return f"{a} {op.value} {b}"
            if (isinstance(a, Token) and a.type == "L_PAR") and (isinstance(b, Token) and b.type == "R_PAR"):
                return f"({op})"
            raise ValueError(f"Unknown 3-item label_expr pattern: {items}")
        raise ValueError(f"Invalid label expression: {items}")

    def boolean(self, items):
        val = items[0].value
        return "t" if val in ["true", "t"] else "f"


def build_automata_states(parsed_body: Dict[str, Any]) -> List[AutomataState]:
    result_states: List[AutomataState] = []
    for chunk in parsed_body.get("states", []):
        state_info = chunk["state"]
        state_label = state_info["label"]
        doc_string = state_info["dstring"]
        acc_sig_list = state_info["acc_sig"] if state_info["acc_sig"] is not None else []

        transitions_list: List[AutomataTransition] = []
        for edge_info in chunk["edges"]:
            edge_label = edge_info["label"]
            edge_acc_sig = edge_info["acc_sig"] if edge_info["acc_sig"] is not None else []
            trans = AutomataTransition(
                label=edge_label,
                acc_sig=edge_acc_sig,
                destination=edge_info["destination"]
            )
            transitions_list.append(trans)

        state_obj = AutomataState(
            state_id=state_info["state_id"],
            acc_sig=acc_sig_list,
            transitions=transitions_list,
            label=state_label,
            docString=doc_string
        )
        result_states.append(state_obj)

    return result_states


class HOAParser:
    __slots__ = ["parser"]

    def __init__(self):
        self.parser = Lark(hoa_grammar, parser='lalr', transformer=HOA_Transformer())

    def __call__(self, hoa_format_ldba):
        parsed_HOA = self.parser.parse(hoa_format_ldba)
        header = parsed_HOA["header"]
        body = parsed_HOA["body"]
        ldba = build_automata_states(body)
        return {
            'header': header,
            'body': ldba
        }
