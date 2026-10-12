"""Independent KKT active-set oracle from edge/path incidence; stdlib only."""
import itertools,json,math,random,subprocess,sys,tempfile
from pathlib import Path
base=Path(__file__).resolve().parents[1]
out=Path(sys.argv[1]) if len(sys.argv)>1 else Path(tempfile.mkdtemp(prefix='erebos-traffic-'))
out.mkdir(parents=True,exist_ok=True)
models={'teaching':([10,0,0,10,0],[0,45,45,0,0],12), 'original':([10,1,1,10,1],[0,50,50,0,10],20)}
A=[[1,0,1],[1,0,0],[0,1,0],[0,1,1],[0,0,1]]
def linear(mat,rhs):
    v=[list(row)+[b] for row,b in zip(mat,rhs)]
    for i in range(len(v)):
        pivot=max(range(i,len(v)),key=lambda j:abs(v[j][i]))
        if abs(v[pivot][i])<1e-12:return None
        v[i],v[pivot]=v[pivot],v[i]
        d=v[i][i];v[i]=[x/d for x in v[i]]
        for j in range(len(v)):
            if j!=i:
                d=v[j][i];v[j]=[x-d*y for x,y in zip(v[j],v[i])]
    return [row[-1] for row in v]
def oracle(name,q,opened,policy):
    slopes,ints,_=models[name]
    if q==0:return [0,0,0]
    n=3 if opened else 2
    factor=1 if policy=='selfish' else 2
    H=[[factor*sum(A[e][i]*slopes[e]*A[e][j] for e in range(5)) for j in range(n)] for i in range(n)]
    b=[sum(A[e][i]*ints[e] for e in range(5)) for i in range(n)]
    for size in range(1,n+1):
        for used in itertools.combinations(range(n),size):
            mat=[[H[i][j] for j in used]+[-1] for i in used]+[[1]*size+[0]]
            ans=linear(mat,[-b[i] for i in used]+[q])
            if ans is None:continue
            f=[0]*n
            for i,x in zip(used,ans[:-1]):f[i]=x
            grad=[b[i]+sum(H[i][j]*f[j] for j in range(n)) for i in range(n)]
            if min(f)<-1e-8 or any(grad[i]<ans[-1]-1e-8 for i in range(n) if i not in used):continue
            return f+[0]*(3-n)
    raise AssertionError(('no KKT point',name,q,opened,policy))
rng=random.Random(1968)
cases=[]
for name,(_,_,maximum) in models.items():
    boundary=[0,1e-12,2,3,4,4.5,6,8,9,maximum]
    boundary += ([2.25,4.5,3,9] if name=='teaching' else [40/22,40/9,80/22,80/9,80/31])
    qs=[maximum*i/2000 for i in range(2001)]+[q+eps for q in boundary for eps in [-1e-9,0,1e-9] if q+eps>=0]+[rng.uniform(0,maximum) for _ in range(200)]
    for q,opened,policy in itertools.product(qs,[False,True],['selfish','coordinated']):cases.append([name,q,opened,policy])
js="const fs=require('fs'),B=require('./src/traffic/model.js'); const inputs=JSON.parse(fs.readFileSync(0,'utf8'));process.stdout.write(JSON.stringify(inputs.map(([m,q,s,p])=>B.solve(B.MODELS[m],q,s,p))));"
run=subprocess.run(['node','-e',js],input=json.dumps(cases),text=True,capture_output=True,cwd=base,check=True)
results=json.loads(run.stdout)
max_flow_error=max_node_error=max_ue_residual=max_so_residual=max_cost_error=0
for (name,q,opened,policy),r in zip(cases,results):
    expected=oracle(name,q,opened,policy)
    err=max(abs(a-b) for a,b in zip(expected,r['flows']));max_flow_error=max(max_flow_error,err)
    assert err<1e-8,(name,q,opened,policy,expected,r)
    assert all(f>=-1e-12 for f in r['flows'])
    u,v,z=r['flows'];ef=[sum(a*f for a,f in zip(row,r['flows'])) for row in A]
    assert max(abs(x-y) for x,y in zip(ef,r['edges']))<1e-10
    node_err=max(abs(ef[0]+ef[2]-q),abs(ef[0]-ef[1]-ef[4]),abs(ef[2]+ef[4]-ef[3]),abs(ef[1]+ef[3]-q))
    max_node_error=max(max_node_error,node_err);assert node_err<1e-8
    slopes,ints,_=models[name];cost=sum(f*(a*f+b) for f,a,b in zip(ef,slopes,ints))
    max_cost_error=max(max_cost_error,abs(cost-r['total']));assert abs(cost-r['total'])<1e-7
    if policy=='selfish':max_ue_residual=max(max_ue_residual,r['regret']);assert r['regret']<1e-8
    else:
        max_so_residual=max(max_so_residual,r['optimalResidual']);assert r['optimalResidual']<1e-8
        old=(models[name][1][1]+(models[name][0][0]+models[name][0][1])*q/2)*q
        assert cost<=old+1e-7
    assert r['mean'] is None if q==0 else abs(r['mean']-cost/q)<1e-8
# Fixed cases from read primary sources, and the original max-vs-mean distinction.
lookup={(m,q,s,p):r for (m,q,s,p),r in zip(cases,results)}
assert lookup['teaching',4,False,'selfish']['mean']==65
assert lookup['teaching',4,True,'selfish']['mean']==80
assert lookup['original',6,False,'selfish']['mean']==83
assert lookup['original',6,True,'selfish']['mean']==92
assert lookup['original',6,True,'selfish']['flows']==[2,2,2]
assert lookup['original',20,True,'selfish']['flows']==[10,10,0]
assert lookup['original',2,True,'coordinated']['mean']<52 # total optimum differs from original max-time example
summary={'status':'PASS','cases':len(cases),'seed':1968,'oracle':'independent edge-incidence KKT active-set enumeration','max_flow_difference':max_flow_error,'max_node_conservation_error':max_node_error,'max_equilibrium_residual':max_ue_residual,'max_optimality_residual':max_so_residual,'max_edge_vs_route_cost_difference':max_cost_error,'source_cases':{'teaching_q4':'65→80','original_q6':'83→92; (2,2,2)','original_q20':'shortcut unused; 160'},'limitations':'Finite sampled sweep plus analytic KKT oracle, not a real traffic validation. Flow epsilon in display diagnostics: 1e-10.'}
(out/'model-tests.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
