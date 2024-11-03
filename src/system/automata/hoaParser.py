from lark import Lark, Transformer, Tree, Token
from dataclasses import dataclass

hoa_grammar = r"""
    start: header "--BODY--" body "--END--"

    header: version tool? name? owl_args? start_state acc_name acceptance properties? ap_decl

    version: "HOA:" /v\d+/
    tool: "tool:" ESCAPED_STRING+
    name: "name:" ESCAPED_STRING
    owl_args: "owlArgs:" ESCAPED_STRING+
    start_state: "Start:" INT
    acc_name: "acc-name:" ("generalized-Buchi" INT | "Buchi")
    acceptance: "Acceptance:" INT acceptance_cond*
    properties: ("Properties:" LOWER_STRING+)+
    ap_decl: "AP:" INT (ESCAPED_STRING)*

    acceptance_cond: "Inf(" INT ")" ("&" "Inf(" INT ")")*

    body: state*
    state: "State:" INT transition* 
    transition: "[" label_expr "]" INT acc_sig?

    label_expr: expr
    expr: factor (LOGIC_OP factor)*
    factor: LOGIC_NOT factor
          | L_PAR expr R_PAR
          | INT
          | IDENTIFIER
    acc_sig: "{" INT+ "}"

    IDENTIFIER: /[a-zA-Z_][0-9a-zA-Z_-]*/
    STRING: /[a-zA-Z_-]+/
    LOWER_STRING: /[0-9a-z_-]+/
    LOGIC_OP: "&" | "|"
    LOGIC_NOT: "!"
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

    def header(self, items):
        return {
            'version': items[0],
            'tool': items[1] if len(items) > 1 else None,
            'name': items[2] if len(items) > 2 else None,
            'owl_args': items[3] if len(items) > 3 else None,
            'start_state': items[4],
            'acc_name': items[5],
            'acceptance': items[6],
            'properties': items[7],
            'ap_decl': items[8]
        }

    def body(self, items):
        return {'states': items}

    def state(self, items):
        return {
            'state_id': items[0],
            'transitions': items[1:]
        }

    def transition(self, items):
        return {
            'label': items[0],
            'destination': items[1],
            'acc_sig': items[2] if len(items) > 2 else None
        }

    def acceptance_cond(self, items):
        return [f"{i}" for i in items]

    def ap_decl(self, items):
        count = items[0]  # Number of atomic propositions
        propositions = {items[i].replace('"', ''): i - 1 for i in range(1, len(items))}
        return {'count': count, 'propositions': propositions}


@dataclass
class HOAAutomataTransition:
    label: str
    destination: str
    accepting_signature: list[str]

    def __post_init__(self):
        if isinstance(self.label, Token):
            self.label = str(self.label.value)
        if isinstance(self.destination, Token):
            self.destination = str(self.destination.value)
        if self.label in ["t"]:
            self.label = "any"


    def __str__(self):
        return f"{self.label} -> ({self.destination})" + '{' + ', '.join(self.accepting_signature) + '}'


@dataclass
class HOAAutomataState:
    state_id: str
    transitions: list[HOAAutomataTransition]

    def __str__(self):
        return f"{'(' + self.state_id + ')':<6}" + ("\n" + 6 * " ").join([f"-> {tr}" for tr in self.transitions])


class HOAParsedHeaderHelper:
    @staticmethod
    def extract_start_state_id(parsed_tree):
        return str(parsed_tree['header']['start_state'].children[0].value)

    @staticmethod
    def extract_accepting_sink_sets_id(parsed_tree):
        return [
            str(ch)
            for ch in parsed_tree['header']['acceptance'].children[1:][0]
        ]

    @staticmethod
    def extract_atomic_propositions_to_symbol(parsed_tree):
        return {
            int(v): str(k)
            for k, v in parsed_tree['header']['ap_decl']['propositions'].items()
        }

    @staticmethod
    def extract_useful_header_info(parsed_tree):
        return {
            'start_state_id': HOAParsedHeaderHelper.extract_start_state_id(parsed_tree),
            'accepting_sink_sets_id': HOAParsedHeaderHelper.extract_accepting_sink_sets_id(parsed_tree),
            'atomic_symbol_to_propositions': HOAParsedHeaderHelper.extract_atomic_propositions_to_symbol(parsed_tree)
        }


class HOAParsedBodyHelper:
    @staticmethod
    def _extract_state_id(parsed_state):
        return parsed_state['state_id'].value

    @staticmethod
    def _label_walk_helper(transition_label):
        """
        Recursively walks through the parsed tree of a transition label
        and converts it into a string representation.
        """
        if isinstance(transition_label, Tree):
            return "".join([HOAParsedBodyHelper._label_walk_helper(child) for child in transition_label.children])
        elif isinstance(transition_label, Token):
            return transition_label.value
        return str(transition_label)

    @staticmethod
    def _extract_acc_sig(acc_sig):
        if acc_sig is None:
            return []
        return [
            ch.value for ch in acc_sig.children
        ]

    @staticmethod
    def extract_transitions(state_transitions):
        return [
            HOAAutomataTransition(
                label=HOAParsedBodyHelper._label_walk_helper(tr['label']),
                destination=tr['destination'],
                accepting_signature=HOAParsedBodyHelper._extract_acc_sig(tr['acc_sig'])
            )
            for tr in state_transitions
        ]

    @staticmethod
    def extract_states(parsed_tree):
        return [
            HOAAutomataState(
                state_id=HOAParsedBodyHelper._extract_state_id(st),
                transitions=HOAParsedBodyHelper.extract_transitions(st['transitions'])
            )
            for st in parsed_tree['body']['states']
        ]


class HOAParser:
    __slots__ = ["parser"]

    def __init__(self):
        self.parser = Lark(hoa_grammar, parser='lalr', transformer=HOA_Transformer())

    def __call__(self, hoa_format_ldba):
        ldba = self.parser.parse(hoa_format_ldba.replace("properties", "Properties"))
        return {
            'header': HOAParsedHeaderHelper.extract_useful_header_info(ldba),
            'states': HOAParsedBodyHelper.extract_states(ldba)
        }
