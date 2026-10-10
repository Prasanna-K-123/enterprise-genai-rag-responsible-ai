"""Bounded arithmetic verification, not semantic entailment or Python execution.

Every non-whitelisted literal must occur in a cited retrieved source. This
prevents unsupported numbers and executable code, but does not prove that a
number belongs to the requested entity, year or unit. Those remain evaluated
failure modes, not a claim of this guard.
"""
import ast
import math
import operator
import re

OPS = {ast.Add: operator.add, ast.Sub: operator.sub,
       ast.Mult: operator.mul, ast.Div: operator.truediv}
CONSTANTS = {0., 1., 2., 3., 4., 5., 10., 12., 100.}
NUMBER = re.compile(r'(?<![\w.])[-+]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?![\w.])')


def source_numbers(text):
    values = set()
    for m in NUMBER.finditer(str(text)):
        value = float(m.group().replace(',', ''))
        # Accountancy parentheses are a negative-value notation.
        left, right = text[:m.start()].rstrip(), text[m.end():].lstrip()
        if left.endswith('(') and right.startswith(')'):
            value = -abs(value)
        values.add(value)
    return values


def verify(proposal, sources):
    if not isinstance(proposal, dict) or set(proposal) != {'answer', 'expression', 'sources'}:
        raise ValueError('Exact answer/expression/sources schema required')
    expression, cited = proposal['expression'], proposal['sources']
    if not isinstance(cited, list) or any(type(x) is not str for x in cited):
        raise ValueError('Citation IDs must be a list of strings')
    if expression is None:
        if proposal['answer'] is not None or cited:
            raise ValueError('A refusal must contain no answer or citations')
        return dict(refused=True, reason='model_refusal')
    if type(expression) is not str or not expression or len(expression) > 240:
        raise ValueError('Bounded arithmetic expression required')
    if not cited or len(set(cited)) != len(cited) or any(k not in sources for k in cited):
        raise ValueError('Missing, repeated or unretrieved citation')
    numbers = set().union(*(source_numbers(sources[k]) for k in cited))
    tree = ast.parse(expression, mode='eval')
    if sum(1 for _ in ast.walk(tree)) > 64:
        raise ValueError('Expression too complex')
    operands = []

    def visit(node, depth=0):
        if depth > 8:
            raise ValueError('Expression too deep')
        if isinstance(node, ast.Constant) and type(node.value) in {int, float}:
            value = float(node.value)
            if not math.isfinite(value) or abs(value) > 1e16:
                raise ValueError('Invalid literal')
            if value not in CONSTANTS and not any(math.isclose(value, n, rel_tol=0, abs_tol=1e-9) for n in numbers):
                raise ValueError('Unsupported numeric operand')
            operands.append(dict(value=value, whitelisted_constant=value in CONSTANTS))
            return value
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            # Signed literals must match their sign in the source. An arbitrary
            # unary minus on a supported positive value is not a fact citation.
            if isinstance(node.operand, ast.Constant) and type(node.operand.value) in {int, float}:
                signed = float(node.operand.value) * (-1 if isinstance(node.op, ast.USub) else 1)
                return visit(ast.Constant(value=signed), depth + 1)
            raise ValueError('Unary operator requires a numeric literal')
        if isinstance(node, ast.BinOp) and type(node.op) in OPS:
            a, b = visit(node.left, depth + 1), visit(node.right, depth + 1)
            if isinstance(node.op, ast.Div) and abs(b) < 1e-12:
                raise ValueError('Zero or near-zero divisor')
            value = OPS[type(node.op)](a, b)
            if not math.isfinite(value) or abs(value) > 1e16:
                raise ValueError('Nonfinite or excessive result')
            return value
        raise ValueError('Only numeric literals and + - * / are allowed')

    value = visit(tree.body)
    return dict(refused=False, answer=value, sources=cited, operands=operands,
                guarantee='Syntax and numeric occurrence only; entity/period/unit meaning is not established')
