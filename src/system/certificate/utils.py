import re
from typing import Dict

from ..action import SystemDecomposedControlPolicy, PolicyType
from ..automata.sub_graph import AutomataState
from ..polynomial.equation import Equation


def infix_to_prefix(expression: str) -> str:
    """
    Convert infix expression to prefix expression with explicit parentheses. Steps of the algorithm:
    1. Reverse the infix expression and swap parentheses.
    2. Convert the reversed infix expression to postfix expression (using shunting yard algorithm).
    3. Reverse the postfix expression to get the prefix expression.
    """
    _precedence = {'!': 3, '&': 2, '|': 1}
    _associativity = {'!': 'R', '&': 'L', '|': 'L'}
    expression = expression.replace(' ', '')

    # Step 1
    expression = expression[::-1]
    expression = expression.translate(str.maketrans('()', ')('))

    # Step 2
    stack = []
    postfix = []
    for char in expression:
        if char.isalnum():  # Operand
            postfix.append(char)
        elif char == '(':  # Left parenthesis in the reversed expression
            stack.append(char)
        elif char == ')':  # Right parenthesis in the reversed expression
            while stack and stack[-1] != '(':
                postfix.append(stack.pop())
            stack.pop()  # Remove '('
        else:  # Operator
            while (stack and stack[-1] != '(' and
                   (_precedence[char] < _precedence[stack[-1]] or
                    (_precedence[char] == _precedence[stack[-1]] and _associativity[char] == 'L'))):
                postfix.append(stack.pop())
            stack.append(char)
    while stack:
        postfix.append(stack.pop())

    # Step 3
    prefix_stack = []
    for token in postfix:
        if token.isalnum():  # Operand
            prefix_stack.append(token)
        else:  # Operator
            if token == '!':  # Unary operator
                operand = prefix_stack.pop()
                expression = f'({token} {operand})'
                prefix_stack.append(expression)
            else:  # Binary operator
                operand2 = prefix_stack.pop()
                operand1 = prefix_stack.pop()
                expression = f'({token} {operand1} {operand2})'
                prefix_stack.append(expression)

    return prefix_stack[0]


def get_policy_action_given_current_abstract_state(current_state: AutomataState, decomposed_control_policy: SystemDecomposedControlPolicy) -> Dict[str, Equation]:
    if decomposed_control_policy.action_dimension == 0:
        return {}
    if current_state.is_accepting():
        policy = decomposed_control_policy.get_policy(PolicyType.BUCHI, 0)
    else:
        policy = decomposed_control_policy.get_policy(PolicyType.REACH)
    return policy()


def _replace_keys_with_values(s, dictionary):
    pattern = re.compile("|".join(re.escape(key) for key in dictionary.keys()))
    result = pattern.sub(lambda match: dictionary[match.group(0)], s)
    return result
