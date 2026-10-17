"""Noise-free falsification tests for overbroad localization claims. No audio."""
from pathlib import Path
from datetime import datetime, timezone
import csv,json,math,random,time,sys
HERE=Path(__file__).resolve().parent;OUT=HERE.parent/'results';OUT.mkdir(exist_ok=True)
sys.path.insert(0,str(HERE.parent/'src'));from sphere import hrtf
A=1e6*.18/343
rad=math.radians

def dot(a,b):return sum(x*y for x,y in zip(a,b))
def norm(v):return math.sqrt(dot(v,v))
def unit(v):
 n=norm(v);return [x/n for x in v]
def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def direction(az,el=0):return [math.cos(rad(el))*math.sin(rad(az)),math.cos(rad(el))*math.cos(rad(az)),math.sin(rad(el))]
def baseline(yaw):return [math.cos(rad(yaw)),-math.sin(rad(yaw)),0]
def delay(az,yaw=0,el=0):return A*dot(direction(az,el),baseline(yaw))

started=datetime.now(timezone.utc);timer=time.perf_counter();rows=[]
# Claim under test: head yaw always identifies which front/back source is present.
# Falsifier: a moving source follows the alternative reflection at every pose.
for yaw_i in range(-180,181):
 yaw=yaw_i/4;front_world=30;moving_world=150+2*yaw
 front=delay(front_world,yaw);moving=delay(moving_world,yaw);fixed_back=delay(150,yaw)
 rows.append({'head_yaw_deg':yaw,'fixed_front_world_deg':front_world,'fixed_back_world_deg':150,'moving_back_world_deg':moving_world,'fixed_front_delay_us':front,'fixed_back_delay_us':fixed_back,'moving_mirror_delay_us':moving,'moving_minus_front_us':moving-front})
max_residual=max(abs(row['moving_minus_front_us']) for row in rows)
assert max_residual<1e-10
assert abs(next(row for row in rows if row['head_yaw_deg']==20)['fixed_back_delay_us']-next(row for row in rows if row['head_yaw_deg']==20)['fixed_front_delay_us'])>300
# Stronger check: a perfectly symmetric sphere with antipodal receivers preserves
# the entire complex-response pair for the matching-incidence trajectory.
max_sphere_residual=0;cases=0
for yaw in [-45,-20,0,20,45]:
 mu1=dot(direction(30),baseline(yaw));mu2=dot(direction(150+2*yaw),baseline(yaw))
 for f in [50,500,1000,4000,8000]:
  for sign in [-1,1]:
   max_sphere_residual=max(max_sphere_residual,abs(hrtf(f,sign*mu1)-hrtf(f,sign*mu2)));cases+=1
assert max_sphere_residual<1e-11
# Finite-range extension: both individual path lengths, not just their difference,
# match under reflection about the current receiver baseline. Same emission timing.
max_finite_path_residual=0;finite_path_cases=0
for source_range in [.2,2,20]:
 for row in rows:
  n=baseline(row['head_yaw_deg'])
  ua=direction(30);ub=direction(row['moving_back_world_deg'])
  for side in [-1,1]:
   ear=[side*.09*x for x in n]
   pa=math.dist([source_range*x for x in ua],ear)
   pb=math.dist([source_range*x for x in ub],ear)
   max_finite_path_residual=max(max_finite_path_residual,abs(pa-pb));finite_path_cases+=1
assert max_finite_path_residual<1e-12
# Claim under test: yaw contains no elevation information.
# Falsifier: horizontal components determine |elevation| for a stationary unit direction.
elevation=[]
for az in [-150,-80,-30,0,30,80,150]:
 for el in [-80,-60,-30,0,30,60,80]:
  for yaw in [-45,-20,20,45]:
   m0=delay(az,0,el);mh=delay(az,yaw,el);h=rad(yaw)
   x=m0/A;y=(x*math.cos(h)-mh/A)/math.sin(h)
   horizontal=math.hypot(x,y);assert horizontal<=1+1e-12
   abs_el=math.degrees(math.acos(min(1,max(0,horizontal))))
   assert abs(abs_el-abs(el))<2e-6
   assert abs(delay(az,yaw,el)-delay(az,yaw,-el))<1e-10
   elevation.append({'azimuth_deg':az,'elevation_deg':el,'yaw_deg':yaw,'recovered_absolute_elevation_deg':abs_el,'elevation_sign_resolved':False})
# Any two nonparallel baselines share a reflected solution on the unit sphere.
# Independent arbitrary-axis test rather than only a horizontal-yaw special case.
rng=random.Random(20261016);reflections=[];max_reflect_error=0
for i in range(2000):
 n0=unit([rng.uniform(-1,1) for _ in range(3)]);n1=unit([rng.uniform(-1,1) for _ in range(3)])
 normal=cross(n0,n1)
 if norm(normal)<.05:continue
 normal=unit(normal);u=unit([rng.uniform(-1,1) for _ in range(3)])
 reflection=[x-2*dot(u,normal)*v for x,v in zip(u,normal)]
 error=max(abs(dot(n0,u)-dot(n0,reflection)),abs(dot(n1,u)-dot(n1,reflection)),abs(norm(reflection)-1))
 max_reflect_error=max(max_reflect_error,error);assert error<1e-12
 reflections.append(error)
report={'started_utc':started.isoformat(),'ended_utc':datetime.now(timezone.utc).isoformat(),'runtime_seconds':time.perf_counter()-timer,'status':'PASS','kind':'noise-free mathematical counterexamples; no perceptual or acoustic measurements','motion_counterexample':{'head_yaw_range_deg':[-45,45],'samples':len(rows),'fixed_front_world_azimuth_deg':30,'moving_alternative_world_azimuth_rule':'150 + 2*head_yaw_deg','identity':'sin(30-yaw) = sin((150+2*yaw)-yaw)','max_delay_residual_us':max_residual,'finite_individual_path_cases':finite_path_cases,'finite_source_ranges_m':[.2,2,20],'max_finite_individual_path_residual_m':max_finite_path_residual,'sphere_response_cases':cases,'max_sphere_complex_response_residual':max_sphere_residual,'conclusion':'Head yaw alone does not uniquely identify a source if source motion is unconstrained. Stationarity/known source motion is an essential assumption.'},'elevation_counterexample':{'cases':len(elevation),'max_absolute_elevation_error_deg':max(abs(row['recovered_absolute_elevation_deg']-abs(row['elevation_deg'])) for row in elevation),'examples':[row for row in elevation if row['azimuth_deg']==30 and row['yaw_deg']==20],'conclusion':'Yaw can recover absolute elevation in the ideal unit-direction model, while leaving its sign unresolved. No elevation information would be an overstatement.'},'two_arbitrary_baselines':{'seed':20261016,'accepted_random_cases':len(reflections),'minimum_cross_product_norm':.05,'max_residual':max_reflect_error,'conclusion':'Two independent signed dot products generally leave a mirror pair on the sphere, not a unique 3D direction.'},'limits':['The moving alternative is a deliberately constructed possibility, not a prediction that listeners will confuse moving sounds.','Sphere equality assumes antipodal receivers and no pinnae, torso, room or personalized filtering.','Elevation magnitude recovery assumes a stationary source, known baseline length, known sound speed, exact pose/time differences and a unit direction.','Snapshot geometry at each pose; no time-domain moving-source propagation, retarded-time or Doppler solver is implemented.','No browser or audio output used.']}
OUT.mkdir(exist_ok=True)
(OUT/'counterexamples.json').write_text(json.dumps(report,indent=2)+'\n')
with (OUT/'moving-source.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
with (OUT/'elevation-magnitude.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(elevation[0]));w.writeheader();w.writerows(elevation)
print(json.dumps(report,indent=2))
