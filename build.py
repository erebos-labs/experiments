"""Build dependency-free, self-contained experiment pages from original source."""
from pathlib import Path
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
