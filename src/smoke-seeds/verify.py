from pathlib import Path
import subprocess,sys,json,csv,math
HERE=Path(__file__).resolve().parent
for name in ('dose_check.py','washout_counterexample.py','finite_loss_counterexample.py','metadata_design_check.py'):
    subprocess.run([sys.executable,'-B',name],cwd=HERE,check=True)
f=json.loads((HERE/'data/finite-loss-checks.json').read_text())['checks']
assert f['cases']==96 and f['independent_numeric_curve_difference']<1e-12
for name,count in [('washout-counterexample.csv',24),('finite-loss-curves.csv',7),('geo-sample-design.csv',28)]:
    with (HERE/'data'/name).open(newline='') as stream:assert len(list(csv.DictReader(stream)))==count
assert '<script' not in (HERE/'index.html').read_text()
print('PASS calculations and metadata design; no biological replication or rendered-browser claim')
