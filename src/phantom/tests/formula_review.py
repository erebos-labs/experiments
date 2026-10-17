"""Separate coordinate derivation, finite-path check and labeling review; no browser."""
from pathlib import Path
from datetime import datetime
import math,random,json,subprocess,sys
HERE=Path(__file__).resolve().parent;OUT=HERE.parent/'results';OUT.mkdir(exist_ok=True)
A=1e6*.18/343;rad=math.radians

def matvec(m,v):return [sum(x*y for x,y in zip(row,v)) for row in m]
def rz(a):return [[math.cos(a),-math.sin(a),0],[math.sin(a),math.cos(a),0],[0,0,1]]
def rx(a):return [[1,0,0],[0,math.cos(a),-math.sin(a)],[0,math.sin(a),math.cos(a)]]
def ry(a):return [[math.cos(a),0,math.sin(a)],[0,1,0],[-math.sin(a),0,math.cos(a)]]
def vector(az,el):return [math.sin(rad(az))*math.cos(rad(el)),math.cos(rad(az))*math.cos(rad(el)),math.sin(rad(el))]
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def inverse(m0,mh,h):
 x=m0/A;y=(m0*math.cos(rad(h))-mh)/(A*math.sin(rad(h)))
 return math.degrees(math.atan2(x,y)),math.hypot(x,y)
def wrap(a):return (a+180)%360-180

rng=random.Random(20261017);inputs=[];expected=[];far_errors=[]
for _ in range(3000):
 az=rng.uniform(-180,180);el=rng.uniform(-89,89);yaw=rng.uniform(-180,180);tilt=rng.uniform(-60,60)
 v=vector(az,el)
 # Positive yaw means a rightward head turn: Rz(-yaw). Positive baseline tilt
 # means the right receiver moves up: Ry(-tilt), not a pitch about the ear axis.
 n=matvec(rz(-rad(yaw)),matvec(ry(-rad(tilt)),[1,0,0]))
 value=A*dot(v,n);inputs.append({'v':v,'yaw':yaw,'tilt':tilt});expected.append(value)
 R=1000;earR=[.09*x for x in n];earL=[-x for x in earR];source=[R*x for x in v]
 dist=lambda p:math.sqrt(sum((x-y)**2 for x,y in zip(source,p)))
 finite=1e6*(dist(earL)-dist(earR))/343;far_errors.append(abs(finite-value))
# Read-only call of included model functions for comparison, not a second derivation of the same sine expression.
js="const fs=require('fs'),M=require('../src/model.js');const q=JSON.parse(fs.readFileSync(0,'utf8'));process.stdout.write(JSON.stringify(q.map(x=>M.delayVector(x.v,x.yaw,x.tilt))));"
cp=subprocess.run(['node','-e',js],input=json.dumps(inputs),text=True,capture_output=True,cwd=HERE,timeout=10);assert cp.returncode==0,cp.stderr
actual=json.loads(cp.stdout);max_rotation_error=max(abs(x-y) for x,y in zip(actual,expected));assert max_rotation_error<1e-10;assert max(far_errors)<2e-6
pitch_cases=[]
for yaw in [-45,0,45]:
 base=matvec(rz(-rad(yaw)),[1,0,0])
 for pitch in [-60,-20,0,20,60]:
  n=matvec(rz(-rad(yaw)),matvec(rx(rad(pitch)),[1,0,0]))
  assert max(abs(x-y) for x,y in zip(n,base))<1e-15;pitch_cases.append([yaw,pitch])
# Strong sign-convention counterexample: reversing the reported yaw flips front/back
# exactly, even though the inverse has unit norm and zero measurement residual.
sign_tests=[]
for az in range(-179,180):
 for h in [-45,-20,20,45]:
  m0=A*math.sin(rad(az));mh=A*math.sin(rad(az-h));est,n=inverse(m0,mh,-h)
  mirror=wrap(180-az);assert abs(wrap(est-mirror))<1e-10;assert abs(n-1)<1e-12
  sign_tests.append(abs(wrap(est-mirror)))
# The slope is per degree, and front/back derivatives at the initial pose have opposite signs.
derivatives=[]
for az in [-80,-30,0,30,80]:
 for el in [0,30,60]:
  eps=1e-4;f=lambda h:A*math.sin(rad(az-h))*math.cos(rad(el))
  numerical=(f(eps)-f(-eps))/(2*eps);analytic=-A*math.cos(rad(az))*math.cos(rad(el))*math.pi/180
  assert abs(numerical-analytic)<1e-6;derivatives.append(abs(numerical-analytic))
frames=[]
for az,yaw in [(80,45),(-80,45),(45,-45),(0,0),(30,45)]:
 mirror=wrap(180-az)
 def half(a):
  c=math.cos(rad(a-yaw));return 'boundary' if abs(c)<1e-10 else 'front' if c>0 else 'back'
 frames.append({'A_world_azimuth_deg':az,'B_world_azimuth_deg':mirror,'head_yaw_deg':yaw,'A_head_relative_half':half(az),'B_head_relative_half':half(mirror)})
report={'status':'PASS','seed':20261017,'checks':{'rotation_cases':len(inputs),'max_rotation_error_us':max_rotation_error,'finite_path_max_error_us':max(far_errors),'pure_pitch_cases':len(pitch_cases),'reversed_yaw_mirror_cases':len(sign_tests),'max_wrong_pose_error_deg':max(sign_tests),'max_slope_error_us_per_degree':max(derivatives)},'label_cases':frames,'limits':['Numerical geometry only; no browser/audio or human measurements.']}
(OUT/'formula-label-review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
