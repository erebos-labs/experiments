"""Independent rational edge-cost/KKT oracle and one-cell proof boundary case."""
from pathlib import Path
from fractions import Fraction as F
import importlib.util,itertools,json,math,subprocess
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'output';OUT.mkdir(exist_ok=True)
learning=ROOT/'model.js'
query="const B=require(process.argv[1]);let rows=[];for(let key of Object.keys(B.MODELS))for(let q=0;q<=80;q++){let d=q/4;rows.push({key,d,...B.exactEquilibrium(B.MODELS[key],d)})}console.log(JSON.stringify(rows))"
rows=json.loads(subprocess.check_output(['node','-e',query,str(learning)],text=True))
def solve(matrix,rhs):
    a=[list(map(F,row))+[F(v)] for row,v in zip(matrix,rhs)];n=len(a)
    for col in range(n):
        pivot=next((r for r in range(col,n) if a[r][col]),None)
        if pivot is None:return None
        a[col],a[pivot]=a[pivot],a[col];v=a[col][col];a[col]=[x/v for x in a[col]]
        for r in range(n):
            if r!=col:
                v=a[r][col];a[r]=[x-v*y for x,y in zip(a[r],a[col])]
    return [row[-1] for row in a]
# Directed edge/route incidence: SA,AT,SB,BT,AB. No production cost/formula import.
A=[[1,0,1],[1,0,0],[0,1,0],[0,1,1],[0,0,1]]
def oracle(key,d):
    slopes=[10,1,1,10,1] if key=='original' else [10,0,0,10,0]
    intercepts=[0,50,50,0,10] if key=='original' else [0,45,45,0,0]
    H=[[sum(slopes[e]*A[e][i]*A[e][j] for e in range(5)) for j in range(3)] for i in range(3)]
    c=[sum(intercepts[e]*A[e][i] for e in range(5)) for i in range(3)]
    if d==0:return [F(0)]*3
    for mask in range(1,8):
        ids=[i for i in range(3) if mask>>i&1];n=len(ids)
        mat=[[H[i][j] for j in ids]+[-1] for i in ids]+[[1]*n+[0]]
        v=solve(mat,[-c[i] for i in ids]+[d])
        if v is None or any(x<0 for x in v[:-1]):continue
        x=[F(0)]*3
        for i,f in zip(ids,v[:-1]):x[i]=f
        costs=[sum(H[i][j]*x[j] for j in range(3))+c[i] for i in range(3)]
        if all(costs[i]>=v[-1] for i in range(3) if i not in ids):return x
    raise AssertionError((key,d))
errors=[]
for row in rows:
    expected=oracle(row['key'],F(str(row['d'])))
    error=max(abs(float(x)-y) for x,y in zip(expected,row['flows']))
    if not error<1e-12:raise ValueError(f'Equilibrium mismatch: {error}')
    errors.append(error)
result={'learning':{'status':'PASS','independent_rational_KKT_cases':len(rows),'maximum_flow_error':max(errors),'method':'Independent rational edge-incidence KKT oracle uses no production formula. The comparison harness imports production output.'}}
(OUT/'independent-equilibrium.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
