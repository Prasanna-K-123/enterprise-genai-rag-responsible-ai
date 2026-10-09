"""Fail-closed numerical layer for model-proposed structured financial queries.

An LLM may propose the request, but it cannot supply facts, execute Python,
change units or override unsupported periods. Canonical answers are computed
and rendered from a frozen public-filing evidence register.
"""
from pathlib import Path
import csv,json,math

ROOT=Path(__file__).resolve().parents[1]
DIRECT={'revenue','operating_income','depreciation_amortization','interest_expense','cash_from_operations','capital_expenditures'}
DERIVED={'ebitda_proxy','free_cash_flow','ebitda_margin','fcf_margin','ebitda_interest_coverage','revenue_growth'}


def answer(request):
    if not isinstance(request,dict) or set(request)-{'entity','year','metric','unit'}:
        raise ValueError('Only entity, year, metric and unit are accepted')
    if not {'entity','year','metric'}.issubset(request) or request['entity']!='CCL':
        raise ValueError('Unsupported or unspecified entity/metric/year')
    year=request['year'];metric=request['metric']
    if type(year) is not int or year not in {2023,2024,2025} or type(metric) is not str or metric not in DIRECT|DERIVED:
        raise ValueError('Unsupported historical period or metric')
    path=ROOT/'reference/financial_tools/source_register.csv'
    register=list(csv.DictReader(path.open()))
    used=[]
    def fact(name,period=year):
        matches=[r for r in register if r['evidence_set']=='annual_history' and r['metric']==name and r['end']==f'{period}-11-30']
        if len(matches)!=1 or matches[0]['unit']!='USD': raise ValueError('Fact missing, ambiguous or has unsupported units')
        row=matches[0];value=float(row['value_raw'])/1e6
        if not math.isfinite(value): raise ValueError('Non-finite financial fact')
        used.append(dict(metric=name,period_end=row['end'],accession=row['accession'],unit='USDm',value=value,
                         source_url=row['source_url'] or f'https://www.sec.gov/Archives/edgar/data/815097/{row["accession"].replace("-","")}/ccl-20251130.htm',
                         original_filing_sha256=row['source_sha256'] or None))
        return value
    def ebitda(): return fact('operating_income')+fact('depreciation_amortization')
    def fcf(): return fact('cash_from_operations')-fact('capital_expenditures')
    if metric in DIRECT: value=fact(metric);unit='USDm';formula='reported statement value / 1e6'
    elif metric=='ebitda_proxy': value=ebitda();unit='USDm';formula='operating income + depreciation/amortization'
    elif metric=='free_cash_flow': value=fcf();unit='USDm';formula='cash from operations - capital expenditures'
    elif metric=='ebitda_margin': value=ebitda()/fact('revenue');unit='ratio';formula='EBITDA proxy / revenue'
    elif metric=='fcf_margin': value=fcf()/fact('revenue');unit='ratio';formula='free cash flow / revenue'
    elif metric=='ebitda_interest_coverage': value=ebitda()/fact('interest_expense');unit='ratio';formula='EBITDA proxy / interest expense'
    else:
        if year==2023: raise ValueError('Prior fiscal year is absent from the frozen corpus')
        current,prior=fact('revenue'),fact('revenue',year-1)
        value=current/prior-1;unit='ratio';formula='current-year revenue / prior-year revenue - 1'
    output_unit=request.get('unit',unit)
    if unit=='USDm' and output_unit=='USD': value*=1e6
    elif unit=='ratio' and output_unit=='percent': value*=100
    elif output_unit!=unit: raise ValueError('Incompatible requested output unit')
    return dict(entity='CCL',fiscal_year=year,metric=metric,value=value,unit=output_unit,
                formula=formula,evidence=used,snapshot='2026-09-02',
                caveat='Historical filing snapshot; EBITDA is a proxy. Numerical evidence is not semantic validation of arbitrary generated prose.')


if __name__=='__main__':
    import sys
    try: print(json.dumps(answer(json.loads(sys.argv[1])),indent=2))
    except (ValueError,KeyError,TypeError,ZeroDivisionError) as error:
        print(json.dumps(dict(refused=True,reason=str(error))))
        sys.exit(2)
