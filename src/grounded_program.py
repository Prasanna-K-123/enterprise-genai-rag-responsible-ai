"""Source-addressed arithmetic with bounded question contracts.

This checks exact cell/span addresses, copied labels, entity namespace, explicit
row phrases/years, declared units and three recognized calculation shapes. It
does NOT prove general natural-language entailment, source authenticity or
arbitrary reasoning. Unknown/composite intent is refused by the
contract policy rather than labelled verified. The address-only policy is an
ablation on the SAME generated proposal, not a separately trained model.
"""
import ast
from dataclasses import dataclass
import hashlib
import json
import math
import re

YEARS = re.compile(r'\b(?:19|20)\d{2}\b')
NUMBER = r'(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?|\.\d+'
TOKEN = re.compile(r'(?<![\w.])(?:\(?\s*[$€£]?\s*[-+]?)(?:'+NUMBER+r')\s*%?\s*\)?')
SCALAR = re.compile(r'^\(?\s*([$€£]?)\s*([-+]?(?:'+NUMBER+r'))\s*(%?)\s*\)?$')
CONSTANTS = {*range(13), 100, 1000}
OUTPUT_UNITS = {'number', 'ratio', 'percent', 'USD', 'USDm', 'USDbn'}


def norm(text):
    return re.sub(r'\s+', ' ', str(text).strip().lower())


def words(text):
    return ' '.join(re.findall(r'[a-z0-9]+', norm(text)))


def parse_scalar(raw):
    text = str(raw).strip().replace('−', '-').replace('–', '-')
    text = re.sub(r'\s*\([a-z]\)\s*$', '', text, flags=re.I)
    # FinQA's published table transcription can show a negative value twice,
    # e.g. "$ -32.0 ( 32.0 )". Accept only an exact magnitude reconciliation.
    duplicate = re.fullmatch(r'([$€£]?)\s*(-(?:'+NUMBER+r'))\s*\(\s*('+NUMBER+r')\s*\)', text)
    if duplicate:
        if abs(float(duplicate[2].replace(',',''))) != float(duplicate[3].replace(',','')):
            return None
        text = duplicate[1]+duplicate[2]
    m = SCALAR.fullmatch(text)
    if not m or text.count('(') != text.count(')'):
        return None
    value = float(m[2].replace(',', ''))
    if text.startswith('('):
        value = -abs(value)
    percent = bool(m[3])
    if percent:
        value /= 100
    if not math.isfinite(value) or abs(value) > 1e16:
        return None
    return value, m[1], percent


def scale_hint(text):
    text = norm(text)
    for label, scale in [('billions', 1e9), ('millions', 1e6), ('thousands', 1e3)]:
        if re.search(r'(?:\bin\s+|amounts\s+in\s+|[$€£]\s*(?:in\s+)?)'+label, text):
            return scale
    return 1.0


def clean_context(record):
    """Read an allowlist. Gold/program/retrieval-label fields never enter input."""
    identity = str(record['id'])
    entity = identity.split('/')[0]
    table = [[str(c) for c in row] for row in record['table']]
    pre, post = list(map(str, record.get('pre_text', []))), list(map(str, record.get('post_text', [])))
    source = dict(table=table, pre_text=pre, post_text=post)
    digest = hashlib.sha256(json.dumps(source, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()
    caption = ' '.join(table[0]) if table else ''
    # Only explicit table/caption scale language; narrative revenue amounts do
    # not silently establish the units of every table column.
    default_scale = scale_hint(caption)
    if default_scale == 1:
        for text in (pre[-1:] + post[:1]):
            if re.search(r'(?:amounts|dollars|figures|table|[$€£])\s*(?:are\s*)?(?:in\s+)(?:thousands|millions|billions)', norm(text)):
                default_scale = scale_hint(text)
                break
    facts = {}

    def add(ref, raw, row, column, periods, local_scale, location):
        parsed = parse_scalar(raw)
        if parsed is None:
            return
        value, currency, percent = parsed
        label = norm(row)
        rate_row = bool(re.search(r'\b(?:percent|percentage|rate|margin|yield)\b', label))
        if percent:
            dimension, scale, explicit = 'ratio', 1.0, True
        elif rate_row:
            # An unmarked number in a rate row may be 4.5 or .045. Never infer
            # the scale solely from the word rate; use a row-specific unit.
            dimension, scale, explicit = 'report:'+label, 1.0, False
        elif currency or (location['kind']=='table_cell' and re.search(r'\b(?:dollars|usd)\b|\$', norm(caption))):
            code = {'$':'USD', '€':'EUR', '£':'GBP'}.get(currency, 'USD')
            dimension, scale, explicit = 'currency:'+code, local_scale, True
            if 'per share' in label:
                dimension += '/share'; scale = 1.0
        else:
            dimension, scale, explicit = 'report:'+label, 1.0, False
        facts[ref] = dict(ref=ref, raw=str(raw), value=value, row=str(row), column=str(column),
                          periods=sorted(set(periods)), entity=entity, dimension=dimension,
                          scale=scale, unit_explicit=explicit, location=location)

    for i, row in enumerate(table[1:], 1):
        for j, raw in enumerate(row[1:], 1):
            column = table[0][j] if j < len(table[0]) else ''
            periods = list(map(int, YEARS.findall(column)))
            if not periods:
                periods = list(map(int, YEARS.findall(row[0])))
            column_scale = scale_hint(column)
            add(f'r{i}c{j}', raw, row[0], column, periods, column_scale if column_scale!=1 else default_scale,
                dict(kind='table_cell', row=i, column=j))
            if f'r{i}c{j}' in facts and facts[f'r{i}c{j}']['scale'] == 1 and default_scale != 1:
                if facts[f'r{i}c{j}']['dimension'].startswith('currency:') and '/share' not in facts[f'r{i}c{j}']['dimension']:
                    facts[f'r{i}c{j}']['scale'] = default_scale
    for section, paragraphs in [('pre',pre),('post',post)]:
        for i, text in enumerate(paragraphs):
            for j, match in enumerate(TOKEN.finditer(text)):
                raw = match.group().strip()
                parsed = parse_scalar(raw)
                if parsed is None:
                    continue
                # A bare calendar year is metadata, not a financial quantity.
                if not parsed[1] and not parsed[2] and parsed[0].is_integer() and 1900 <= parsed[0] <= 2099:
                    continue
                vicinity = text[max(0,match.start()-65):min(len(text),match.end()+65)]
                periods = list(map(int,YEARS.findall(vicinity)))
                # Multiple nearby years are ambiguous; keep the ambiguity so
                # contract checks refuse instead of assigning a guessed year.
                suffix=re.match(r'\s*(thousand|million|billion)s?\b',text[match.end():],re.I)
                local_scale={'thousand':1e3,'million':1e6,'billion':1e9}[suffix[1].lower()] if suffix else scale_hint(vicinity)
                add(f'{section}{i}n{j}', raw, f'{section}_text[{i}]', '', periods, local_scale,
                    dict(kind='text_span', section=section, paragraph=i, start=match.start(), end=match.end()))
    question = str(record['qa']['question'])
    return dict(id=identity, entity=entity, question=question, source_sha256=digest,
                source=source, facts=facts, contract=question_contract(question))


def question_contract(question):
    text = norm(question)
    years = sorted(set(map(int, YEARS.findall(text))))
    ranged = re.search(r'(?:from|between)\s+((?:19|20)\d{2})\s+(?:to|through|and)\s+((?:19|20)\d{2})', text)
    average = 'average' in text or 'mean' in text
    growth = bool(re.search(r'(?:percent(?:age)?[^?.]{0,35}(?:change|increase|decrease|decline|growth)|(?:change|increase|decrease|decline|growth)[^?.]{0,35}percent|growth rate)', text))
    plain_difference = bool(re.search(r'\b(?:difference|change|increase|decrease)\b', text))
    # Strong policy deliberately handles only these named calculation shapes.
    # Other free-form/composite questions are outside its verification claim.
    composite = bool(re.search(r'\b(?:weighted|compound|cagr|annualized|annualised|percentage points?|percent points?|per annum|if|assuming|without|excluding|adjusted|quarter|quarterly)\b',text))
    if composite or (average and growth):
        kind = 'unsupported'
    elif average:
        kind = 'average'
        if ranged and int(ranged[2])-int(ranged[1]) in range(1,10):
            years = list(range(int(ranged[1]),int(ranged[2])+1))
    elif growth:
        kind = 'decrease' if re.search(r'\b(?:decrease|decline)\b',text) else 'growth'
    elif plain_difference and len(years)==2:
        kind = 'difference'
    else:
        kind = 'unsupported'
    if 'percent' in text or '%' in text:
        unit = 'percent'
    elif re.search(r'\b(?:ratio|fraction)\b',text):
        unit = 'ratio'
    elif re.search(r'\bin\s+billions?\b',text):
        unit = 'USDbn'
    elif re.search(r'\bin\s+millions?\b',text):
        unit = 'USDm'
    else:
        unit = 'number'
    direction = re.search(r'from\s+((?:19|20)\d{2})\s+(?:to|through)\s+((?:19|20)\d{2})',text)
    base_period = int(direction[1]) if direction and kind!='average' else (min(years) if years else None)
    target_period = int(direction[2]) if direction and kind!='average' else (max(years) if years else None)
    return dict(kind=kind, periods=years, base_period=base_period, target_period=target_period, output_unit=unit, question=question,
                scope='Explicit years/units and bounded average/change contracts; not general semantic entailment')


@dataclass(frozen=True)
class Quantity:
    value: float
    dimension: str
    refs: frozenset


def _canonical(tree):
    return ast.dump(tree, annotate_fields=False, include_attributes=False)


def _sum_names(node):
    if isinstance(node,ast.Name):
        return [node.id]
    if isinstance(node,ast.BinOp) and isinstance(node.op,ast.Add):
        return _sum_names(node.left)+_sum_names(node.right)
    raise ValueError('formula_mismatch: average numerator must be a sum of distinct facts')


def contract_measure(facts,question):
    text=' '+words(question)+' '
    labels={words(f['row']) for f in facts.values()
            if f['location']['kind']=='table_cell' and re.search('[a-z]',words(f['row']))
            and ' '+words(f['row'])+' ' in text}
    if len(labels)!=1:
        raise ValueError('measure_phrase_missing_or_ambiguous')
    return next(iter(labels))


def deterministic_contract(context):
    """A simple non-LLM baseline for exactly the declared phrase/year contract.

    Including this baseline avoids attributing elementary table arithmetic to
    neural reasoning. No gold labels, synonyms or reference programs are read.
    """
    contract=context['contract'];facts=context['facts'];kind=contract['kind']
    if kind=='unsupported':raise ValueError('unsupported_question_contract')
    measure=contract_measure(facts,context['question']);years=contract['periods']
    if not years:raise ValueError('period_ambiguous_or_missing')
    selected={}
    for year in years:
        options=[r for r,f in facts.items() if f['location']['kind']=='table_cell'
                 and words(f['row'])==measure and f['periods']==[year]]
        if len(options)!=1:raise ValueError('period_ambiguous_or_missing')
        selected[year]=options[0]
    refs=[selected[y] for y in years]
    if kind=='average':expression='('+'+'.join(refs)+')/'+str(len(refs))
    else:
        if len(years)!=2:raise ValueError('period_mismatch')
        old,new=selected[contract['base_period']],selected[contract['target_period']]
        expression=f'{old}-{new}' if kind=='decrease' else f'{new}-{old}'
        if kind!='difference':expression=f'({expression})/{old}'
    proposal=dict(answer=None,expression=expression,output_unit=contract['output_unit'],entity=context['entity'],
                  bindings=[{k:facts[r][k] for k in ['ref','row','column']} for r in refs])
    return execute(proposal,context,contract_policy=True)


def _validate_contract(tree, refs, facts, contract):
    kind, years = contract['kind'], contract['periods']
    if kind=='unsupported':
        raise ValueError('unsupported_question_contract')
    if any(len(facts[r]['periods'])!=1 for r in refs):
        raise ValueError('period_ambiguous_or_missing')
    selected_years = [facts[r]['periods'][0] for r in refs]
    if not years or set(selected_years)!=set(years):
        raise ValueError('period_mismatch')
    if len(set(norm(facts[r]['row']) for r in refs))!=1:
        raise ValueError('measure_mismatch: bounded contract requires one exact row/span label')
    # This is an explicit phrase contract, not a semantic similarity classifier.
    # Aliases, narrative-only facts and multi-measure questions remain outside
    # the contract instead of being asserted to have equivalent meanings.
    selected_label = words(facts[refs[0]]['row'])
    if contract_measure(facts,contract['question'])!=selected_label:
        raise ValueError('measure_phrase_missing_or_ambiguous')
    if len(selected_years)!=len(set(selected_years)):
        raise ValueError('duplicate_period')
    if kind=='average':
        if not isinstance(tree,ast.BinOp) or not isinstance(tree.op,ast.Div) or not isinstance(tree.right,ast.Constant):
            raise ValueError('formula_mismatch: explicit average division required')
        terms = _sum_names(tree.left)
        if len(terms)<2 or len(terms)!=len(set(terms)) or set(terms)!=set(refs) or type(tree.right.value) not in {int,float} or tree.right.value!=len(terms):
            raise ValueError('formula_mismatch: average must include all requested periods exactly once')
    else:
        if len(years)!=2 or len(refs)!=2:
            raise ValueError('period_mismatch: two-year change required')
        old = next(r for r in refs if facts[r]['periods'][0]==contract['base_period'])
        new = next(r for r in refs if facts[r]['periods'][0]==contract['target_period'])
        numerator = f'{old}-{new}' if kind=='decrease' else f'{new}-{old}'
        expression = numerator if kind=='difference' else f'({numerator})/{old}'
        if _canonical(tree)!=_canonical(ast.parse(expression,mode='eval').body):
            raise ValueError('formula_mismatch: year order or base-period denominator')


def execute(proposal, context, *, contract_policy=False):
    if not isinstance(proposal,dict) or set(proposal)!={'answer','expression','output_unit','entity','bindings'}:
        raise ValueError('schema_mismatch')
    expression, bindings = proposal['expression'], proposal['bindings']
    if expression is None:
        if proposal['answer'] is not None or bindings:
            raise ValueError('inconsistent_refusal')
        return dict(refused=True,reason='model_refusal')
    if type(expression) is not str or not expression or len(expression)>512:
        raise ValueError('expression_bounds')
    if proposal['entity']!=context['entity']:
        raise ValueError('entity_mismatch')
    if proposal['output_unit'] not in OUTPUT_UNITS or not isinstance(bindings,list) or not 1<=len(bindings)<=24:
        raise ValueError('binding_or_unit_bounds')
    facts = context['facts']; refs=[]
    for binding in bindings:
        if not isinstance(binding,dict) or set(binding)!={'ref','row','column'}:
            raise ValueError('binding_schema')
        ref = binding['ref']
        if type(ref) is not str or ref not in facts:
            raise ValueError('unknown_fact')
        if ref in refs:
            raise ValueError('duplicate_binding')
        if binding['row']!=facts[ref]['row'] or binding['column']!=facts[ref]['column']:
            raise ValueError('binding_mismatch')
        if facts[ref]['entity']!=context['entity']:
            raise ValueError('source_entity_mismatch')
        refs.append(ref)
    tree = ast.parse(expression,mode='eval')
    if sum(1 for _ in ast.walk(tree))>128:
        raise ValueError('expression_complexity')
    names = {n.id for n in ast.walk(tree) if isinstance(n,ast.Name)}
    if names != set(refs):
        raise ValueError('unused_or_missing_binding')

    def visit(node,depth=0):
        if depth>10:
            raise ValueError('expression_depth')
        if isinstance(node,ast.Name) and node.id in facts:
            fact=facts[node.id]
            return Quantity(fact['value']*fact['scale'],fact['dimension'],frozenset([node.id]))
        if isinstance(node,ast.Constant) and type(node.value) in {int,float} and node.value in CONSTANTS:
            return Quantity(float(node.value),'ratio',frozenset())
        if isinstance(node,ast.UnaryOp) and isinstance(node.op,(ast.UAdd,ast.USub)):
            q=visit(node.operand,depth+1)
            return Quantity(q.value*(-1 if isinstance(node.op,ast.USub) else 1),q.dimension,q.refs)
        if not isinstance(node,ast.BinOp) or not isinstance(node.op,(ast.Add,ast.Sub,ast.Mult,ast.Div)):
            raise ValueError('unsafe_expression')
        left,right=visit(node.left,depth+1),visit(node.right,depth+1)
        if isinstance(node.op,(ast.Add,ast.Sub)):
            if contract_policy and left.dimension!=right.dimension:
                raise ValueError('unit_mismatch')
            value=left.value+right.value if isinstance(node.op,ast.Add) else left.value-right.value
            dimension=left.dimension
        elif isinstance(node.op,ast.Mult):
            if contract_policy and left.dimension!='ratio' and right.dimension!='ratio':
                raise ValueError('unit_mismatch: compound product outside bounded units')
            value=left.value*right.value
            dimension=right.dimension if left.dimension=='ratio' else left.dimension
        else:
            if abs(right.value)<1e-16:
                raise ValueError('zero_divisor')
            if contract_policy and left.dimension!=right.dimension and right.dimension!='ratio':
                raise ValueError('unit_mismatch')
            value=left.value/right.value
            dimension='ratio' if left.dimension==right.dimension else left.dimension
        if not math.isfinite(value) or abs(value)>1e16:
            raise ValueError('result_bounds')
        return Quantity(value,dimension,left.refs|right.refs)

    q=visit(tree.body)
    unit=proposal['output_unit']
    if contract_policy:
        contract=context['contract']
        _validate_contract(tree.body,refs,facts,contract)
        if unit!=contract['output_unit']:
            raise ValueError('requested_unit_mismatch')
        if unit in {'percent','ratio'} and q.dimension!='ratio':
            raise ValueError('unit_mismatch: dimensionless result required')
        if unit.startswith('USD') and q.dimension!='currency:USD':
            raise ValueError('unit_mismatch: explicit USD source required')
    value=q.value
    if unit=='percent':
        value*=100
    elif q.dimension.startswith('currency:'):
        if unit in {'USD','USDm','USDbn'}:
            value/={'USD':1,'USDm':1e6,'USDbn':1e9}[unit]
        else:
            scales={facts[r]['scale'] for r in refs if facts[r]['dimension']==q.dimension}
            if len(scales)!=1:
                raise ValueError('ambiguous_report_scale')
            value/=next(iter(scales))
    reported=proposal['answer']
    agrees=type(reported) in {int,float} and math.isfinite(reported) and math.isclose(value,reported,rel_tol=1e-6,abs_tol=1e-6)
    return dict(refused=False,answer=value,output_unit=unit,
                execution_value=value/100 if unit=='percent' else value,
                expression=expression,dimension=q.dimension,refs=refs,
                model_numeric_agreement=agrees,provenance=[facts[r] for r in refs],
                contract_checked=contract_policy,
                scope='Exact source addresses/labels/entity namespace; bounded explicit row-phrase/period/formula/unit controls. General natural-language entailment and report authenticity remain unverified.')
