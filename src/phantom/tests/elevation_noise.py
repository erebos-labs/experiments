"""Bounded estimator sensitivity; invented timing errors, no listener predictions."""
from pathlib import Path
from datetime import datetime, timezone
import math,random,json,csv,time
r=Path(__file__).resolve().parent;o=r.parent/'results';o.mkdir(exist_ok=True)
A=180000/343;seed=20261016;rng=random.Random(seed);start=datetime.now(timezone.utc);timer=time.perf_counter()
noise=[(rng.uniform(-15,15),rng.uniform(-15,15))for _ in range(256)]
rows=[];n=0
for yaw in [10,20,45]:
 h=math.radians(yaw)
 for elevation in [0,5,15,30,60,80]:
  estimates=[];inconsistent=0
  for az in range(-180,180,15):
   azr=math.radians(az);e=math.radians(elevation)
   m0=A*math.sin(azr)*math.cos(e);mh=A*math.sin(azr-h)*math.cos(e)
   for n0,nh in noise:
    x=(m0+n0)/A;y=((m0+n0)/A*math.cos(h)-(mh+nh)/A)/math.sin(h)
    q=math.hypot(x,y);inconsistent+=q>1
    estimate=math.degrees(math.acos(min(1,q)))
    assert 0<=estimate<=90
    estimates.append(estimate);n+=1
  ordered=sorted(estimates);err=sorted(abs(v-elevation)for v in estimates)
  rows.append({'yaw_separation_deg':yaw,'true_abs_elevation_deg':elevation,'cases':len(estimates),'inconsistent_unit_direction_fraction':inconsistent/len(estimates),'median_clipped_abs_elevation_deg':ordered[len(ordered)//2],'p95_clipped_absolute_error_deg':err[math.ceil(.95*len(err))-1]})
report={'started_utc':start.isoformat(),'ended_utc':datetime.now(timezone.utc).isoformat(),'runtime_seconds':time.perf_counter()-timer,'status':'PASS','seed':seed,'cases':n,'design':'24 world azimuths x256 shared independent uniform[-15,15]us error pairs x6 elevations x3 yaw separations','estimator':'Unconstrained horizontal inverse; report q>1 inconsistency. For the illustrative magnitude summary only, clip q to1 then acos(q). No constrained fit or statistical confidence claim.','rows':rows,'conclusion':'Noiseless elevation-magnitude identifiability does not guarantee stable magnitude estimates. Clipping changes the estimator and can mask impossible exact-model observations.','limits':['Synthetic errors are invented, not human measurement variability','One seed and a finite angular grid','Summaries pool azimuths and are conditional on this estimator','Up/down sign remains unresolved even with noiseless data','No audio output or listening test']}
(o/'elevation-noise.json').write_text(json.dumps(report,indent=2)+'\n')
with (o/'elevation-noise.csv').open('w',newline='')as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print(json.dumps(report,indent=2))
