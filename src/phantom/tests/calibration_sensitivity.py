"""Exact synthetic nuisance-scale ambiguity; no anatomical claims or audio."""
from pathlib import Path
from datetime import datetime, timezone
import math,json,time
r=Path(__file__).resolve().parent;o=r.parent/'results';o.mkdir(exist_ok=True);start=datetime.now(timezone.utc);timer=time.perf_counter();A=180000/343;rows=[]
# A_true / A_assumed is a synthetic calibration factor, not measured anatomy.
for k in [.9,.95,1,1.05,1.1]:
 for el in [0,15,30,60,80]:
  q=k*math.cos(math.radians(el));apparent=None if q>1+1e-12 else math.degrees(math.acos(min(1,q)))
  max_residual=0
  if apparent is not None:
   for az in range(-180,180,15):
    for yaw in [-45,-20,0,20,45]:
     true=k*A*math.sin(math.radians(az-yaw))*math.cos(math.radians(el))
     alternative=A*math.sin(math.radians(az-yaw))*math.cos(math.radians(apparent))
     max_residual=max(max_residual,abs(true-alternative));assert abs(true-alternative)<1e-10
  rows.append({'true_to_assumed_delay_scale':k,'true_abs_elevation_deg':el,'exact_unit_model_consistent':apparent is not None,'apparent_abs_elevation_deg':apparent,'max_matching_delay_residual_us':max_residual if apparent is not None else None})
report={'started_utc':start.isoformat(),'ended_utc':datetime.now(timezone.utc).isoformat(),'runtime_seconds':time.perf_counter()-timer,'status':'PASS','rows':rows,'identity':'A_true*cos(e_true)=A_assumed*cos(e_alternative). A yaw sequence alone observes this product, so cannot separate elevation magnitude from an unknown delay scale.','parameters':'Synthetic A=d/c scale factors; not measurements of human ear separation or sound speed.','matching_pose_checks_per_consistent_row':120,'example':'A true level source with0.95times assumed delay scale exactly fits +/-acos(0.95)=18.1949degrees in the assumed model.','limits':['Calibration-scale identifiability only, not human perception','No proof this nuisance explains any actual listener results','No audio or acoustic measurements']}
(o/'calibration-sensitivity.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k!='rows'},indent=2))
