from pathlib import Path
import subprocess,sys,xml.etree.ElementTree as ET,json
r=Path(__file__).resolve().parents[1]
if sys.version_info < (3,10): raise SystemExit('Requires Python 3.10 or newer')
node=subprocess.run(['node','-p','process.versions.node'],capture_output=True,text=True,check=True,timeout=10).stdout.strip()
if int(node.split('.')[0]) < 18: raise SystemExit('Requires Node.js 18 or newer')
cmds=[[sys.executable,'-B','scripts/build.py'],['node','--check','src/model.js'],['node','--check','src/ui.js'],['node','tests/test_model.js'],['node','tests/test_ui_logic.js']]+[[sys.executable,'-B',p]for p in ['src/sphere.py','tests/counterexamples.py','tests/formula_review.py','tests/spectral_nuisance.py','tests/elevation_noise.py','tests/calibration_sensitivity.py','tests/test_page.py']]
for cmd in cmds:
 p=subprocess.run(cmd,cwd=r,text=True,capture_output=True,timeout=30)
 print('PASS'if p.returncode==0 else'FAIL', ' '.join(cmd))
 if p.returncode:
  print(p.stdout);print(p.stderr);raise SystemExit(p.returncode)
for p in (r/'results').glob('vector-*.svg'):ET.parse(p)
for filename in ['model-tests.json','ui-logic-tests.json']:
 report=json.loads((r/'results'/filename).read_text());assert report['status']=='PASS'
print('Numerical checks, mock events and SVG XML pass. No browser/audio output checked.')
