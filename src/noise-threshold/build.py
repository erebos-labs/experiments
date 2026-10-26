from pathlib import Path
import json
HERE=Path(__file__).resolve().parent
html=(HERE/'page.template.html').read_text()
for token,name in [('/* CORE */','core.js'),('/* UI */','ui.js')]:
    assert html.count(token)==1
    html=html.replace(token,(HERE/name).read_text())
for token,name in [('/* STUDY */','controls.json'),('/* EXACT */','exact-control.json')]:
    assert html.count(token)==1
    html=html.replace(token,json.dumps({'rows':json.loads((HERE/'data'/name).read_text())['rows']},separators=(',',':')))
(HERE/'index.html').write_text(html)
print('Built noise-threshold/index.html')
