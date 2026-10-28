"""Reproduce the bounded study and build a standalone offline HTML bench."""
from fractions import Fraction
from pathlib import Path
import hashlib
import json
import model as m
import involutions as iq
import groups as g

EXP=Path(__file__).resolve().parent
ART=EXP/'data'


def integer_inverse(matrix):
    n=len(matrix)
    a=[list(map(Fraction,row))+[Fraction(int(i==j)) for j in range(n)] for i,row in enumerate(matrix)]
    for col in range(n):
        pivot=next(i for i in range(col,n) if a[i][col])
        a[col],a[pivot]=a[pivot],a[col]
        factor=a[col][col];a[col]=[x/factor for x in a[col]]
        for i in range(n):
            if i!=col:
                factor=a[i][col];a[i]=[x-factor*y for x,y in zip(a[i],a[col])]
    result=[row[n:] for row in a]
    assert all(x.denominator==1 for row in result for x in row)
    inverse=[[int(x) for x in row] for row in result]
    assert all(sum(matrix[i][k]*inverse[k][j] for k in range(n))==int(i==j) for i in range(n) for j in range(n))
    return inverse


def write_json(name,data):
    (ART/name).write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')


def main():
    ART.mkdir(exist_ok=True)
    source=json.loads((EXP/'source_data.json').read_text())
    assert all(source['gauss'][key]==value for key,value in m.GAUSS.items())
    matrix,arcs=m.gauss_matrix(source['gauss']['conway']);reduced=m.minor(matrix)
    certificate={'diagram':'Knot Atlas K11n34 (mirror convention does not affect the stated counts)',
        'gauss_code':source['gauss']['conway'],'matrix':matrix,'deleted_row':0,'deleted_column':0,
        'reduced_matrix':reduced,'determinant':m.determinant(reduced),
        'integer_inverse':integer_inverse(reduced),
        'claim':'Exactly q constant Fox colorings for every integer q >= 2',
        'proof':'Every crossing row sums to zero. Subtract x[0] from all labels; the remaining 10 labels obey B*y=0. The recorded integer inverse implies y=0 modulo every q. Constant assignments satisfy all original equations.'}
    assert certificate['determinant']==-1
    write_json('conway-certificate.json',certificate)
    references=[]
    for key,preset in m.PRESETS.items():
        counts={str(q):len(m.enumerate_colorings(preset['strands'],preset['word'],q)) for q in range(2,32)}
        for q in range(2,32):
            if m.prime(q):assert counts[str(q)]==m.linear_count(preset['strands'],preset['word'],q)
        arc_matrix,n=m.braid_arc_matrix(preset['strands'],preset['word'])
        assert len(arc_matrix)==n
        references.append({'key':key,**preset,'counts':counts,'determinant':abs(m.determinant(m.minor(arc_matrix)))})
    nulls=[]
    for label,elements in [('S4 transpositions',iq.involutions(4,2)),('A5 double transpositions',iq.involutions(5,4))]:
        table=iq.conjugation_table(elements);assert iq.check_axioms(table)
        counts={}
        for name in ('trefoil','figure8','conway'):
            result=iq.solutions(source['gauss'][name],table)
            counts[name]={'total':len(result['solutions']),'constant':len(table),'seed_assignments':result['assignments']}
        nulls.append({'rule':label,'labels':len(table),'counts':counts})
    group=g.psl(7);base=g.canonical((0,1,-1,1),7);labels=g.conjugacy_class(group,base,7);forward,backward=g.tables(labels,7)
    group_results={}
    for name,pd in source['pd'].items():
        result=g.count_fixed(pd,forward,backward)
        equations,n,edge_arcs=g.pd_constraints(pd)
        group_results[name]={**result,'total':len(labels)*result['normalized_count'],'constant':len(labels),'nonconstant':len(labels)*(result['normalized_count']-1),'pd':pd,'equations':equations}
    assert group_results['conway']['normalized_count']==13
    assert group_results['kinoshita_terasaka']['normalized_count']==7
    witness={'group':'PSL(2,7)','group_size':len(group),'label_rule':'Conjugacy class of order-3 elements; matrices are identified up to sign modulo 7',
       'base_element':base,'labels':labels,'forward_table':forward,'backward_table':backward,
       'count_normalization':'Fix the first propagation seed to color 0, enumerate the other seeds, multiply count by 56. Simultaneous group conjugation acts transitively on labels and bijects every fixed-color fiber.',
       'results':group_results,'source_reference':'Eisermann (2007), Example 2.18; normalized counts 13 and 7'}
    other_classes={}
    class_controls=[]
    for order,raw in [(2,(0,1,-1,0)),(7,(1,1,0,1))]:
        qlabels=g.conjugacy_class(group,g.canonical(raw,7),7)
        qforward,qbackward=g.tables(qlabels,7)
        class_results={}
        for name in ('conway','kinoshita_terasaka'):
            pd=source['pd'][name]
            result=g.count_fixed(pd,qforward,qbackward)
            equations,n,edges=g.pd_constraints(pd)
            expected=1 if order==2 else 15
            assert result['normalized_count']==expected
            class_results[name]={**result,'total':len(qlabels)*result['normalized_count'],
               'constant':len(qlabels),'nonconstant':len(qlabels)*(result['normalized_count']-1),
               'pd':pd,'equations':equations}
        other_classes[str(order)]={'labels':qlabels,'results':class_results,
           'numerical_reference':'Direct bounded control calculation' if order==2 else 'Eisermann (2007), Example 2.17: normalized count 15 for each knot'}
    for order,entry in [('2',other_classes['2']),('3',witness),('7',other_classes['7'])]:
        class_controls.append({'order':int(order),'labels':len(entry['labels']),
           'conway':entry['results']['conway']['total'],'kinoshita_terasaka':entry['results']['kinoshita_terasaka']['total']})
    witness['other_classes']=other_classes
    write_json('matrix-colorings.json',witness)
    study={'references':references,'involutory_nulls':nulls,'label_class_controls':class_controls,
       'conway_fox_certificate':{'determinant':-1,'file':'conway-certificate.json','all_moduli':True},
       'group_counts':{name:{k:v[k] for k in ('normalized_count','total','constant','nonconstant','assignments')} for name,v in group_results.items()},
       'limits':['Small chosen diagrams; not arbitrary knot recognition','No claim of a new invariant or new mathematical result','Fox and general conjugation are different coloring rules','Mirror labels not assigned; no longitude or smooth-sliceness calculation']}
    write_json('study.json',study)
    html_data={'presets':m.PRESETS,'references':references,'certificate':{'reduced_matrix':reduced,'determinant':-1},
       'group':{'labels':labels,'results':group_results},'other_group_classes':other_classes}
    template=(EXP/'bench.template.html').read_text()
    html=template.replace('__ENGINE__',(EXP/'engine.js').read_text()).replace('__DATA__',json.dumps(html_data).replace('</',r'<\/'))
    if '__MATRIX_RULE__' in html:html=html.replace('__MATRIX_RULE__',(EXP/'matrix_rule.js').read_text())
    assert '__DATA__' not in html and '__ENGINE__' not in html
    (EXP/'index.html').write_text(html)
    print(json.dumps({'reference_rows':len(references),'Conway_Fox_determinant':-1,
       'Conway_matrix_total':group_results['conway']['total'],'Conway_matrix_nonconstant':group_results['conway']['nonconstant'],
       'KT_matrix_total':group_results['kinoshita_terasaka']['total'],'offline_HTML_bytes':len(html.encode()),
       'offline_HTML_sha256':hashlib.sha256(html.encode()).hexdigest()},indent=2))


if __name__=='__main__':main()
