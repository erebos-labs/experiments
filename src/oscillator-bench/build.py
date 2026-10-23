"""Build the self-contained oscillator page from inspectable local sources."""
from pathlib import Path
p=Path(__file__).resolve().parent
html=(p/'page.template.html').read_text()
for old,name,tag in [('<link rel="stylesheet" href="styles.css">','styles.css','style'),('<script src="model.js"></script>','model.js','script'),('<script src="app.js"></script>','app.js','script')]:
    if html.count(old)!=1: raise ValueError('Expected exactly one asset token: '+name)
    html=html.replace(old,'<'+tag+'>'+(p/name).read_text()+'</'+tag+'>')
(p/'index.html').write_text(html)
