from pathlib import Path
r=Path(__file__).resolve().parents[1];s=r/'src';page=(s/'page.html').read_text(encoding='utf-8')
for marker,name in [('STYLE','style.css'),('MODEL','model.js'),('UI','ui.js')]:
 assert page.count('/* '+marker+' */')==1
 page=page.replace('/* '+marker+' */',(s/name).read_text(encoding='utf-8'))
(r/'index.html').write_bytes(page.encode('utf-8'))
print('Built self-contained index.html')
