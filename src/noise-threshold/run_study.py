"""Frozen primary study. Outputs are all local; no network or dependencies."""
import csv,json,math,platform,time
from pathlib import Path
from model import *

OUT=Path(__file__).resolve().parent/'data'

def save(name,data):
    (OUT/name).write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')

def main():
    begun=time.perf_counter()
    a=.25;t=1;n=256;base=20261025
    rows=[]
    for j in range(41):
        s=j/10
        expected=theory(a,t,s,n)
        batch=ensemble(a,t,s,base,n,128)
        d=detection(a,t,s,base,n,128,256)
        rows.append({'sigma':s,'theory':expected,'batches':batch,'detection':d})
    limits={}
    for label,args in {'no_signal':(0,1,.8),'retuned_clean':(.25,0,0),'huge_noise':(.25,1,1e6),'suprathreshold_clean':(1.5,1,0)}.items():
        limits[label]={'parameters':args,'theory':theory(*args,n),'ensemble':ensemble(*args,base,n,128),'detection':detection(*args,base,n,128,256)}
    # Retune threshold across a finite grid at every noise strength using analytic BA.
    retuning=[]
    for s in (0,.2,.4,.6,.8,1,2,4):
        candidates=[(theory(a,j/100,s,n)['balanced_accuracy'],j/100) for j in range(-150,151,5)]
        best=max(candidates,key=lambda x:x[0]);retuning.append({'sigma':s,'best_grid_threshold':best[1],'best_grid_accuracy':best[0],'fixed_accuracy':theory(a,1,s,n)['balanced_accuracy']})
    sample_counts=[]
    for count in (64,256,1024):
        for s in (0,.4,.8,1.5,4):sample_counts.append({'n':count,'sigma':s,**detection(a,1,s,base,count,128,256)})
    fixtures=[]
    for a0,t0,s0,seed,n0 in ((.25,1,.8,20261025,256),(0,1,2,0,64),(1,0,0,42,128),(.5,-.5,.2,4294967295,64),(2,2,1e6,123,64)):
        fixtures.append({'args':[a0,t0,s0,seed,n0],'simulation':simulate(a0,t0,s0,seed,n0,True),'theory':theory(a0,t0,s0,n0)})
    save('reference-fixtures.json',fixtures)
    result={'parameters':{'amplitude':a,'threshold':t,'n':n,'period':64,'base_seed':base,'ensemble_batches':128,'calibration_batches':128,'test_batches':256,'noise_grid':[0,4,.1]},'rows':rows,'controls':limits,'retuning':retuning,'sample_counts':sample_counts,'python':platform.python_version(),'duration_seconds':time.perf_counter()-begun}
    save('study.json',result)
    with (OUT/'sweep.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['sigma','phase_hit','phase_false','balanced_accuracy','phase_mi','projection','null_crossing','mse','power','record_false_alarm'])
        writer.writeheader()
        for r in rows:writer.writerow({'sigma':r['sigma'],**{k:r['theory'][k] for k in ('phase_hit','phase_false','balanced_accuracy','phase_mi','projection','null_crossing','mse')},'power':r['detection']['power']['rate'],'record_false_alarm':r['detection']['false_alarm']['rate']})
    print(json.dumps({'seconds':result['duration_seconds'],'rows':len(rows),'grid_maxima':{k:max(rows,key=lambda r:r['theory'][k])['sigma'] for k in ('balanced_accuracy','phase_mi','projection')},'detection_max':max(rows,key=lambda r:r['detection']['power']['rate'])['sigma']},indent=2))

if __name__=='__main__':main()
