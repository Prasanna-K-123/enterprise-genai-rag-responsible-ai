"""Typed financial arithmetic; explicit requests, not general language QA.

Source facts must come from the separately verified capture. Company identity,
concept, observation dates, annual duration, accession and currency are part of
every lookup. The engine never treats a filing FY field as an observation year.
"""
import ast
from decimal import Decimal, localcontext
import hashlib
import json
import math
import re
from datetime import date

UNITS = {'USD': Decimal(1), 'USDk': Decimal(1000),
         'USDm': Decimal(1000000), 'USDbn': Decimal(1000000000),
         'ratio': Decimal(1), 'percent': Decimal('.01')}
OPS = {'lookup', 'sum', 'mean', 'subtract', 'growth', 'ratio'}
REQUEST_KEYS = {'entity', 'accession', 'operation', 'operands', 'output_unit'}
SELECTOR_KEYS = {'concept', 'start', 'end'}


def sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':')).encode()).hexdigest()


def decimal(value):
    if type(value) not in {str, int, float}:
        raise ValueError('numeric_type')
    try:
        number = Decimal(str(value))
    except Exception as error:
        raise ValueError('numeric_syntax') from error
    if not number.is_finite() or abs(number) > Decimal('1e18'):
        raise ValueError('numeric_bounds')
    return number


def validate_request(request):
    if type(request) is not dict or set(request) != REQUEST_KEYS:
        raise ValueError('request_schema')
    if type(request['entity']) is not str or not re.fullmatch(r'\d{10}', request['entity']):
        raise ValueError('entity_namespace')
    if type(request['accession']) is not str or not re.fullmatch(r'\d{10}-\d{2}-\d{6}', request['accession']):
        raise ValueError('accession_namespace')
    op = request['operation']
    if type(op) is not str or op not in OPS:
        raise ValueError('unsupported_operation')
    if type(request['output_unit']) is not str or request['output_unit'] not in UNITS:
        raise ValueError('unsupported_output_unit')
    operands = request['operands']
    if type(operands) is not list or not 1 <= len(operands) <= 10:
        raise ValueError('operand_bounds')
    if op == 'lookup' and len(operands) != 1 or op in {'subtract', 'growth', 'ratio'} and len(operands) != 2:
        raise ValueError('operation_arity')
    if op in {'mean', 'sum'} and len(operands) < 2:
        raise ValueError('operation_arity')
    for operand in operands:
        if type(operand) is not dict or set(operand) != SELECTOR_KEYS:
            raise ValueError('selector_schema')
        if type(operand['concept']) is not str or not re.fullmatch(r'us-gaap:[A-Za-z][A-Za-z0-9]*', operand['concept']):
            raise ValueError('concept_namespace')
        try:
            start, end = date.fromisoformat(operand['start']), date.fromisoformat(operand['end'])
        except (TypeError, ValueError) as error:
            raise ValueError('observation_dates') from error
        if not 350 <= (end-start).days <= 380:
            raise ValueError('annual_duration_required')
    if len({sha(o) for o in operands}) != len(operands):
        raise ValueError('duplicate_selector')
    if op in {'growth', 'mean'} and len({o['concept'] for o in operands}) != 1:
        raise ValueError('same_measure_required')
    if op == 'mean':
        years = sorted(date.fromisoformat(o['end']).year for o in operands)
        if years != list(range(years[0], years[-1]+1)):
            raise ValueError('complete_annual_range_required')
    if op == 'growth' and request['output_unit'] not in {'percent', 'ratio'}:
        raise ValueError('dimensionless_growth_output')
    if op == 'ratio' and request['output_unit'] not in {'percent', 'ratio'}:
        raise ValueError('dimensionless_ratio_output')
    if op not in {'growth', 'ratio'} and request['output_unit'] not in {'USD', 'USDk', 'USDm', 'USDbn'}:
        raise ValueError('currency_output_required')


def select(request, facts):
    validate_request(request)
    selected = []
    for operand in request['operands']:
        matches = [f for f in facts if f['entity'] == request['entity']
                   and f['accession'] == request['accession']
                   and all(f[k] == operand[k] for k in SELECTOR_KEYS)]
        if len(matches) != 1:
            raise ValueError('missing_or_ambiguous_source_context')
        fact = matches[0]
        if fact['unit'] != 'USD' or fact['dimensions'] != []:
            raise ValueError('explicit_consolidated_USD_required')
        if fact['form'] != '10-K':
            raise ValueError('annual_filing_required')
        decimal(fact['value'])
        selected.append(fact)
    if request['operation'] in {'growth', 'ratio'} and decimal(selected[0 if request['operation']=='growth' else 1]['value']) <= 0:
        raise ValueError('nonpositive_base_requires_explicit_policy')
    return selected


def expression_for(operation, refs):
    if operation == 'lookup': return refs[0]
    if operation == 'sum': return '('+'+'.join(refs)+')'
    if operation == 'mean': return '('+'+'.join(refs)+')/'+str(len(refs))
    if operation == 'subtract': return refs[0]+'-'+refs[1]
    if operation == 'growth': return '('+refs[1]+'-'+refs[0]+')/'+refs[0]
    if operation == 'ratio': return refs[0]+'/'+refs[1]
    raise ValueError('unsupported_operation')


def propose(request, facts):
    selected = select(request, facts)
    refs = [f['ref'] for f in selected]
    return {'entity': request['entity'], 'refs': refs,
            'expression': expression_for(request['operation'], refs),
            'output_unit': request['output_unit'], 'answer': None}


def tree_shape(node):
    return ast.dump(node, annotate_fields=False, include_attributes=False)


def sum_refs(node):
    if isinstance(node, ast.Name): return [node.id]
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return sum_refs(node.left)+sum_refs(node.right)
    raise ValueError('sum_formula_required')


def validate_formula(tree, operation, refs):
    if operation in {'sum', 'mean'}:
        numerator = tree
        if operation == 'mean':
            if not isinstance(tree, ast.BinOp) or not isinstance(tree.op, ast.Div) or not isinstance(tree.right, ast.Constant) or type(tree.right.value) is not int or tree.right.value != len(refs):
                raise ValueError('mean_divisor')
            numerator = tree.left
        terms = sum_refs(numerator)
        if sorted(terms) != sorted(refs): raise ValueError('complete_measure_period_sum_required')
        return
    forms = [expression_for(operation, refs)]
    if operation == 'growth': forms.append(refs[1]+'/'+refs[0]+'-1')
    if tree_shape(tree) not in {tree_shape(ast.parse(s, mode='eval').body) for s in forms}:
        raise ValueError('operation_or_operand_order_mismatch')


def evaluate(expression, by_ref):
    if type(expression) is not str or not 1 <= len(expression) <= 512:
        raise ValueError('expression_bounds')
    try: tree = ast.parse(expression, mode='eval')
    except (SyntaxError, ValueError) as error: raise ValueError('expression_syntax') from error
    if sum(1 for _ in ast.walk(tree)) > 128: raise ValueError('expression_complexity')
    def visit(node, depth=0):
        if depth > 10: raise ValueError('expression_depth')
        if isinstance(node, ast.Name) and node.id in by_ref:
            return decimal(by_ref[node.id]['value'])
        if isinstance(node, ast.Constant) and type(node.value) is int and node.value in {*range(11), 100, 1000}:
            return Decimal(node.value)
        if not isinstance(node, ast.BinOp) or not isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
            raise ValueError('unsafe_expression')
        left, right = visit(node.left, depth+1), visit(node.right, depth+1)
        if isinstance(node.op, ast.Add): value = left+right
        elif isinstance(node.op, ast.Sub): value = left-right
        elif isinstance(node.op, ast.Mult): value = left*right
        else:
            if right == 0: raise ValueError('zero_divisor')
            value = left/right
        return decimal(str(value))
    with localcontext() as context:
        context.prec = 40
        return visit(tree.body), tree.body


def execute(proposal, request, facts, *, policy='semantic', evidence_sha256=None):
    if policy == 'semantic' and (evidence_sha256 is None or sha(facts) != evidence_sha256):
        raise ValueError('unverified_or_changed_source_capture')
    if type(proposal) is not dict or set(proposal) != {'entity','refs','expression','output_unit','answer'}:
        raise ValueError('proposal_schema')
    if type(proposal['refs']) is not list or any(type(r) is not str for r in proposal['refs']) or not 1 <= len(proposal['refs']) <= 10 or len(proposal['refs']) != len(set(proposal['refs'])):
        raise ValueError('binding_bounds')
    by_ref = {f['ref']: f for f in facts}
    if len(by_ref) != len(facts): raise ValueError('duplicate_source_reference')
    if any(r not in by_ref for r in proposal['refs']): raise ValueError('unknown_source_reference')
    if type(proposal['output_unit']) is not str or proposal['output_unit'] not in UNITS:
        raise ValueError('unsupported_output_unit')
    refs = proposal['refs']
    if policy == 'reported':
        value = decimal(proposal['answer'])
        tree = None
    else:
        value, tree = evaluate(proposal['expression'], by_ref)
        names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
        if names != set(refs): raise ValueError('unused_or_missing_binding')
        if policy == 'semantic':
            selected = select(request, facts)
            expected = [f['ref'] for f in selected]
            if proposal['entity'] != request['entity']: raise ValueError('entity_mismatch')
            if proposal['output_unit'] != request['output_unit']: raise ValueError('requested_unit_mismatch')
            if set(refs) != set(expected): raise ValueError('entity_concept_period_accession_mismatch')
            validate_formula(tree, request['operation'], expected)
        elif policy != 'addressed': raise ValueError('unknown_policy')
        with localcontext() as context:
            context.prec = 40
            value = value/UNITS[proposal['output_unit']]
    return {'refused': False, 'answer': str(value), 'entity': proposal['entity'],
            'output_unit': proposal['output_unit'], 'expression': proposal['expression'],
            'refs': refs, 'evidence': [by_ref[r] for r in refs],
            'request_sha256': sha(request), 'policy': policy,
            'reported_numeric_agreement': proposal['answer'] is not None and math.isclose(float(value),float(decimal(proposal['answer'])),rel_tol=1e-10,abs_tol=1e-10)}


def answer(request, facts, *, evidence_sha256=None):
    """Return a complete typed answer or an explicit refusal; no model needed."""
    try: return execute(propose(request,facts),request,facts,evidence_sha256=evidence_sha256)
    except ValueError as error: return {'refused': True,'reason':str(error)}
