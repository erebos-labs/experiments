"""Build dependency-free, self-contained experiment pages from original source."""
from pathlib import Path
import json
base=Path(__file__).resolve().parent
for folder,target,tokens in [
    ('clocks','local-clocks',[('/*MODEL*/','model.js'),('/*SEQUENCE*/','sequence.js'),('/*SYNTH*/','synth.js')]),
    ('traffic','shortcut-trap',[('/* STYLES */','style.css'),('/* MODEL */','model.js'),('/* UI */','ui.js')])]:
    src=base/'src'/folder
    html=(src/'page.template.html').read_text()
    for token,name in tokens:
        assert html.count(token)==1,token
        html=html.replace(token,(src/name).read_text())
    (base/'docs'/target/'index.html').write_text(html)
    print('Built docs/'+target+'/index.html')
src=base/'src/riffle'
html=(src/'page.template.html').read_text()
data=json.loads((src/'data.json').read_text())
html=html.replace('__DATA__',json.dumps(data,separators=(',',':'))).replace('__SCRIPT__',(src/'ui.js').read_text())
(base/'docs/riffle-shuffles/index.html').write_text(html)
print('Built docs/riffle-shuffles/index.html')

# Keep the independently scoped standalone module reproducible in this collection.
import subprocess, sys, shutil
subprocess.run([sys.executable, '-B', str(base/'src/phantom/scripts/build.py')], check=True)
shutil.copyfile(base/'src/phantom/index.html', base/'docs/phantom-sound/index.html')
print('Built docs/phantom-sound/index.html')

shutil.copyfile(base/'src/flower-evidence/index.html',base/'docs/flower-evidence/index.html')
print('Built docs/flower-evidence/index.html')

shutil.copyfile(base/'src/spinning-disk/index.html',base/'docs/spinning-disk/index.html')
print('Built docs/spinning-disk/index.html')

subprocess.run([sys.executable, '-B', str(base/'src/route-learning/build.py'), '--check'], check=True)
shutil.copyfile(base/'src/route-learning/index.html',base/'docs/route-learning/index.html')
print('Built docs/route-learning/index.html')

# Source guide: no new model or interactive application.
from html import escape
source = base/'src/square-ice'
readme = (source/'README.md').read_text(encoding='utf-8')
links = ''.join('<li><a href="https://github.com/erebos-labs/experiments/blob/main/src/square-ice/'+name+'">'+escape(name)+'</a></li>' for name in ['README.md','SOURCES.md','checks.py','ice.py','loops.cpp','soft_ice.py'])
page = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="referrer" content="no-referrer"><title>Square ice · Source guide</title><style>body{margin:0;background:#f5f3ec;color:#203a3c;font-family:system-ui,sans-serif;line-height:1.65}main{max-width:850px;margin:auto;padding:24px}a{color:#00665f}a:focus-visible{outline:3px solid #9b6c00;outline-offset:3px}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:inherit}li{margin:.4em 0}h1{line-height:1.2;font-size:clamp(28px,6vw,44px)}</style></head><body><main><nav><a href="../index.html">Back to the collection</a></nav><h1>Square ice: source guide</h1><p>Established arrow-model ideas and finite executable checks. No new theorem or quantitative water-ice claim. This page presents the included README verbatim as text.</p><h2>Source files</h2><p>The source links open the repository on GitHub. The full source is also available in a downloaded repository.</p><ul>'+links+'</ul><h2>Module README</h2><pre>'+escape(readme)+'</pre><footer>AI assistance acknowledged. Source references and limitations are retained in the module. No third-party images, fonts or paper bodies bundled. GitHub hosting may log visits; this page adds no scripts or telemetry.</footer></main></body></html>\n'
(base/'docs/square-ice/index.html').write_text(page,encoding='utf-8')
print('Built docs/square-ice/index.html')

# Same coin: exact overlapping-pattern probabilities, no external dependencies.
subprocess.run([sys.executable, '-B', str(base/'src/same-coin/build.py')], check=True)
shutil.copyfile(base/'src/same-coin/index.html',base/'docs/same-coin/index.html')
print('Built docs/same-coin/index.html')

# Kelvin wake measurement explorer: dependency-free linear-wave model.
subprocess.run([sys.executable, '-B', str(base/'src/kelvin-wakes/build.py')], check=True)
shutil.copyfile(base/'src/kelvin-wakes/index.html',base/'docs/kelvin-wakes/index.html')
print('Built docs/kelvin-wakes/index.html')

# Coupled Stuart–Landau oscillators: finite, dimensionless educational model.
subprocess.run([sys.executable, '-B', str(base/'src/oscillator-bench/build.py')], check=True)
shutil.copyfile(base/'src/oscillator-bench/index.html',base/'docs/oscillator-bench/index.html')
print('Built docs/oscillator-bench/index.html')

# Finite stochastic-resetting teaching model.
subprocess.run([sys.executable, '-B', str(base/'src/restart-bargain/build.py')], check=True)
shutil.copyfile(base/'src/restart-bargain/index.html',base/'docs/restart-bargain/index.html')
print('Built docs/restart-bargain/index.html')
