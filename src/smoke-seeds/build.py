from pathlib import Path
from html import escape
import re
HERE=Path(__file__).resolve().parent
readme=(HERE/'README.md').read_text()
css="body{margin:0;background:#f5f3ec;color:#203a3c;font:16px/1.65 system-ui,sans-serif}main{max-width:900px;margin:auto;padding:28px 20px}h1{font-size:clamp(30px,6vw,48px);line-height:1.15}a{color:#00665f}a:focus-visible{outline:3px solid #9b6c00;outline-offset:4px}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:inherit}li{margin:.5em 0}footer{border-top:1px solid #ccd7d1;margin-top:28px;padding-top:16px;font-size:13px}"
citations=''.join('<li><a href="'+escape(url,quote=True)+'">'+escape(label)+'</a></li>' for label,url in re.findall(r'\[([^\]]+)\]\((https://[^)]+)\)',readme))
links=''.join('<li><a href="https://github.com/erebos-labs/experiments/blob/main/src/smoke-seeds/'+name+'">'+escape(name)+'</a></li>' for name in ('README.md','dose_check.py','washout_counterexample.py','finite_loss_counterexample.py','metadata_design_check.py','data/finite-loss-curves.csv','data/geo-sample-design.csv'))
page='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="referrer" content="no-referrer"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; base-uri \'none\'; form-action \'none\'"><title>What does smoke tell a seed?</title><style>'+css+'</style></head><body><main><nav><a href="../index.html">Back to the collection</a></nav><h1>What does smoke tell a seed?</h1><p>A source guide and constructed washout counterexamples. Identical emergence curves can conceal different retained states. No biological replication or new discovery is claimed.</p><h2>Code and derived tables</h2><ul>'+links+'</ul><h2>Primary sources</h2><ul>'+citations+'</ul><h2>Model, sources and limitations</h2><pre>'+escape(readme)+'</pre><footer>Built with AI assistance. No third-party publication bodies or assets bundled. Hosting may log visits; this page adds no scripts or telemetry.</footer></main></body></html>\n'
(HERE/'index.html').write_text(page)
print('Built smoke-seeds/index.html')
