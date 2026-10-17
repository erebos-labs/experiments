"""Unknown source filtering: silent frequency-by-frequency identifiability check."""
from pathlib import Path
from datetime import datetime, timezone
import math,cmath,json,csv,sys,time
r=Path(__file__).resolve().parent;o=r.parent/'results';o.mkdir(exist_ok=True)
sys.path.insert(0,str(r.parent/'src'));from sphere import hrtf
start=datetime.now(timezone.utc);timer=time.perf_counter();rows=[]
def pair(f,az,b):
 t=math.radians(az);b=math.radians(b)
 return tuple(hrtf(f,s*math.sin(t)*math.cos(b)-math.cos(t)*math.sin(b))for s in [-1,1])
for backset in [0,5,10,20]:
 for f in [50,200,500,1000,2000,4000,8000]:
  al,ar=pair(f,30,backset);bl,br=pair(f,150,backset)
  sb=al/bl # choose a different common source spectrum to match the left exactly
  left_residual=abs(sb*bl-al)/abs(al)
  right_residual=abs(sb*br-ar)/abs(ar)
  # Minimize ||b*s-a||² across both complex receivers, independently per frequency.
  best=(bl.conjugate()*al+br.conjugate()*ar)/(abs(bl)**2+abs(br)**2)
  least_squares=math.sqrt((abs(best*bl-al)**2+abs(best*br-ar)**2)/(abs(al)**2+abs(ar)**2))
  ratio_residual=abs(al/ar-bl/br)
  assert left_residual<1e-14
  if backset==0:assert right_residual<1e-12 and least_squares<1e-12
  rows.append({'backset_deg':backset,'frequency_hz':f,'left_relative_residual_after_exact_left_match':left_residual,'right_relative_residual_after_exact_left_match':right_residual,'best_two_channel_relative_l2_residual':least_squares,'complex_interaural_ratio_difference':ratio_residual})
assert max(v['best_two_channel_relative_l2_residual']for v in rows if v['backset_deg']==10)>.05
report={'started_utc':start.isoformat(),'ended_utc':datetime.now(timezone.utc).isoformat(),'runtime_seconds':time.perf_counter()-timer,'status':'PASS','cases':len(rows),'model':'Same rigid sphere, far field, 30/150 degree sources, receivers with specified rearward backset','identity':'A common nonzero source spectrum cancels in L/R. One channel can be matched by changing source spectrum; both generally cannot when interaural ratios differ.','fitting':'Complex least-squares common factor at each frequency, an optimistic algebraic nuisance fit. No causality, energy, stability or real-signal construction imposed.','max_left_relative_residual':max(v['left_relative_residual_after_exact_left_match']for v in rows),'ten_degree_rows':[v for v in rows if v['backset_deg']==10],'limits':['Not an audible difference or human detection prediction','No audio generated; source factors need not form a realizable causal filter','Zeros/silent frequency bins do not provide a ratio; all sampled nonzero responses used','No head, pinna or room measurements']}
(o/'spectral-nuisance.json').write_text(json.dumps(report,indent=2)+'\n')
with (o/'spectral-nuisance.csv').open('w',newline='')as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print(json.dumps(report,indent=2))
