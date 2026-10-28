from pathlib import Path
r=Path(__file__).resolve().parent
art=r
page=(r/'page.html').read_text()
for marker,name in [('/*MODEL*/','model.js'),('/*APP*/','app.js')]:
    code=(r/name).read_text()
    if '</script' in code.lower():raise ValueError('Unsafe inline script terminator')
    assert page.count(marker)==1
    page=page.replace(marker,code)
(art/'index.html').write_text(page)
print(f'Built index.html: {len(page.encode())} bytes')
