"""Negative controls: optimization must never hide a release failure."""
from pathlib import Path
import os,shutil,subprocess,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parent
class ValidationControls(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        for name in ['build.py','verify_equilibrium.py','model.js','app.js','style.css','page.html','index.html']:
            shutil.copyfile(ROOT/name,self.root/name)
    def tearDown(self):self.temp.cleanup()
    def reject_both(self,script,*args):
        for optimize in [[],['-O']]:
            p=subprocess.run([sys.executable,*optimize,'-B',script,*args],cwd=self.root,capture_output=True,text=True,timeout=20)
            self.assertNotEqual(p.returncode,0,p.stdout+p.stderr)
    def test_stale_page_rejected_with_and_without_optimization(self):
        p=self.root/'index.html';p.write_bytes(p.read_bytes()+b'\n<!-- stale negative control -->\n');before=p.read_bytes()
        self.reject_both('build.py','--check');self.assertEqual(p.read_bytes(),before)
    def test_duplicate_token_rejected_with_and_without_optimization(self):
        p=self.root/'page.html';p.write_text(p.read_text()+'<script src="app.js"></script>')
        self.reject_both('build.py')
    def test_corrupt_equilibrium_rejected_with_and_without_optimization(self):
        p=self.root/'model.js';p.write_text(p.read_text()+"\nconst real=module.exports.exactEquilibrium;module.exports.exactEquilibrium=(...a)=>({...real(...a),flows:[0,0,0]});\n")
        self.reject_both('verify_equilibrium.py')
if __name__=='__main__':unittest.main(verbosity=2)
