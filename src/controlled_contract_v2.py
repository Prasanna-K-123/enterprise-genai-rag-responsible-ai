"""Post-hoc, deterministic controlled-language table calculator.

Version 1 remains immutable for its registered experiment. This separate
version addresses diagnosed errors; it is not a new held-out result, a model
policy comparison, general question understanding or source authentication.
"""
import copy
import re

from .grounded_program import clean_context, execute, norm, words

YEAR = r'(?:19|20)\d{2}'
PERIOD = rf'(?P<start>{YEAR})\s*(?:-|to|through|and)\s*(?P<end>{YEAR})'
PREFIX = r'what (?:is|was|were) (?:the )?'
CHANGE = re.compile(PREFIX + r'(?P<operation>(?:percentage|percent) (?:change|increase|growth|decrease|decline)|growth rate|change|difference|increase|decrease) (?:in|of) (?P<measure>.+?) (?:from|between) ' + PERIOD)
AVERAGE = re.compile(PREFIX + r'average (?:of )?(?P<measure>.+?) (?:from|between) ' + PERIOD)
CONSIDERING = re.compile(r'considering the years ' + PERIOD + r' what (?:is|was) (?:the )?average (?:of )?(?P<measure>.+)')
SCALE = {'thousand': 1e3, 'million': 1e6, 'billion': 1e9}


def question_contract_v2(question):
    text = norm(question).replace('–', '-').replace('—', '-')
    text = re.sub(r'[?,]', ' ', text).strip(' .')
    text = re.sub(r'\s+', ' ', text)
    unit = 'number'
    suffix = re.search(r' in (thousands?|millions?|billions?|dollars|usd)$', text)
    if suffix:
        label = suffix[1].rstrip('s')
        unit = {'million': 'USDm', 'billion': 'USDbn', 'dollar': 'USD', 'usd': 'USD'}.get(label)
        if unit is None:
            raise ValueError('unsupported_output_unit')
        text = text[:suffix.start()]
    # A unit requested before the measure is still only an OUTPUT unit. It
    # must not be used to guess the scale of the source table.
    inline = re.search(r'\b(change|difference|increase|decrease) in (millions?|billions?) (?:of|in) ', text)
    if inline:
        if unit != 'number':
            raise ValueError('ambiguous_requested_unit')
        unit = 'USDm' if inline[2].startswith('million') else 'USDbn'
        text = text[:inline.start()] + inline[1] + ' in ' + text[inline.end():]
    match = CONSIDERING.fullmatch(text) or AVERAGE.fullmatch(text) or CHANGE.fullmatch(text)
    if match is None:
        raise ValueError('unsupported_controlled_question')
    start, end = int(match['start']), int(match['end'])
    if start == end:
        raise ValueError('period_ambiguous_or_missing')
    operation = match.groupdict().get('operation') or 'average'
    if operation == 'average':
        if not 1 <= end - start <= 9:
            raise ValueError('average_range_bounds')
        periods = list(range(start, end + 1))
        kind = 'average'
    else:
        periods = sorted([start, end])
        if 'percent' in operation or operation == 'growth rate':
            if unit != 'number':
                raise ValueError('ambiguous_requested_unit')
            unit = 'percent'
            kind = 'decrease' if any(x in operation for x in ['decrease', 'decline']) else 'growth'
        else:
            # Plain decreases use base-target. A plain increase or change
            # uses target-base. No relative-percent inference from "change".
            kind = 'decrease_amount' if operation == 'decrease' else 'difference'
    return dict(kind=kind, periods=periods, base_period=start, target_period=end,
                output_unit=unit, measure=words(match['measure']), question=question)


def table_scale(context):
    table = context['source']['table']
    caption = words(table[0][0]) if table and table[0] else ''
    # Whole caption patterns, not an unrelated narrative amount. Captions
    # without a scale remain unknown for requested currency conversion.
    match = re.fullmatch(r'(?:(?:amounts|figures|dollars|usd) (?:are )?)?(?:in )?(thousands?|millions?|billions?)(?: of (?:dollars|usd))?(?: except (?:percentages|per share amounts))?', caption)
    if not match:
        return None
    return SCALE[match[1].rstrip('s')]


def controlled_contract_v2(record):
    context = clean_context(record)
    contract = question_contract_v2(context['question'])
    matching_rows = {f['location']['row'] for f in context['facts'].values()
                     if f['location']['kind'] == 'table_cell' and words(f['row']) == contract['measure']}
    if len(matching_rows) != 1 or contract['measure'] in {'total', 'balance', 'amount', 'value'}:
        raise ValueError('whole_measure_missing_or_ambiguous')
    row = next(iter(matching_rows))
    selected = {}
    for year in contract['periods']:
        options = [copy.deepcopy(f) for f in context['facts'].values()
                   if f['location']['kind'] == 'table_cell' and f['location']['row'] == row and f['periods'] == [year]]
        if len(options) != 1:
            raise ValueError('period_ambiguous_or_missing')
        fact = options[0]
        # This version supports bare-year columns only. Mixed scale, quarter,
        # restatement or footnote headers need a separate explicit contract.
        if not re.fullmatch(YEAR, norm(fact['column'])):
            raise ValueError('unsupported_column_context')
        scale = table_scale(context)
        if scale is not None and fact['dimension'].startswith('currency:') and '/share' not in fact['dimension']:
            fact['scale'] = scale
        if contract['output_unit'].startswith('USD'):
            if fact['dimension'] != 'currency:USD' or scale is None:
                raise ValueError('unknown_currency_or_source_scale')
        selected[year] = fact
    base = selected[contract['base_period']]
    if contract['kind'] in {'growth', 'decrease'} and base['value'] <= 0:
        raise ValueError('nonpositive_growth_base_requires_explicit_policy')
    refs = [selected[year]['ref'] for year in contract['periods']]
    if contract['kind'] == 'average':
        expression = '(' + '+'.join(refs) + ')/' + str(len(refs))
    else:
        old, new = base['ref'], selected[contract['target_period']]['ref']
        expression = f'{old}-{new}' if contract['kind'] in {'decrease', 'decrease_amount'} else f'{new}-{old}'
        if contract['kind'] in {'growth', 'decrease'}:
            expression = f'({expression})/{old}'
    # Retain the fixed source and its digest; expose only the single exact row
    # to the shared AST validator after complete-question/row matching.
    context['facts'] = {fact['ref']: fact for fact in selected.values()}
    context['contract'] = {**contract, 'kind': 'difference' if contract['kind'] == 'decrease_amount' else contract['kind']}
    if contract['kind'] == 'decrease_amount':
        context['contract']['base_period'], context['contract']['target_period'] = contract['target_period'], contract['base_period']
    proposal = dict(answer=None, expression=expression, entity=context['entity'],
                    output_unit=contract['output_unit'],
                    bindings=[{key:context['facts'][ref][key] for key in ['ref', 'row', 'column']} for ref in refs])
    result = execute(proposal, context, contract_policy=True)
    result.update(contract_version='controlled-language-v2-posthoc', source_sha256=context['source_sha256'],
                  scope='Deterministic complete-question grammar and whole-row identity; bounded table arithmetic. Dollar-symbol convention inherited from v1. General language semantics, issuer aliases, source authenticity and all currencies/transcriptions remain unverified. Post-hoc development, not fresh held-out performance.')
    return result
