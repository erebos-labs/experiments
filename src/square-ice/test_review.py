import unittest
import ice
import json,subprocess,sys,tempfile,shutil
from pathlib import Path
from loop_fixture import canonical_rows
ROOT=Path(__file__).resolve().parent
from soft_ice import partition
class ReviewRegressions(unittest.TestCase):
    def test_dimensions_rejected_before_work(self):
        for function,args in [(ice.torus_count,(100000,1)),(ice.torus_count,(2,-1)),(ice.free_count,(100000,)),(ice.domain_count,(0,)),(ice.asm_formula,(-1,)),(ice.boundary_count,(1,100000,0,0,[],[]))]:
            with self.assertRaises(ValueError):function(*args)
        self.assertEqual(ice.asm_formula(0),1)
    def test_tiny_positive_q_is_rejected_not_false_zero(self):
        with self.assertRaisesRegex(ValueError,'numerical domain'):partition(2,1e-200,3,0,1,0)
        self.assertGreater(partition(2,.001,3,0,1,0),0)
        self.assertIsInstance(partition(3,0,7,0,0,1),int)
        self.assertEqual(partition(3,1,7,0,0,1),2**12)
    def test_exact_loop_matrix_and_schema(self):
        rows=[json.loads(x) for x in (ROOT/'data/loops.jsonl').read_text().splitlines()]
        self.assertEqual(len(canonical_rows(rows)),9)
        bad=[rows[:-1],[rows[0]]*9,[dict(row,extra=1) for row in rows],[]]
        for value in bad:
            with self.assertRaises(ValueError):canonical_rows(value)
    def test_optimized_validators_fail_before_reporting_pass(self):
        for script in ['checks.py','verify_loops.py','boundary_paths.py','generate_fixtures.py','soft_ice.py']:
            p=subprocess.run([sys.executable,'-O','-B',script],cwd=ROOT,capture_output=True,text=True,timeout=10)
            self.assertNotEqual(p.returncode,0,script)
            self.assertIn('without -O or PYTHONOPTIMIZE',p.stderr)
    def test_corrupt_loop_fixture_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'data').mkdir()
            for n in ['verify_loops.py','loop_fixture.py','ice.py']:shutil.copyfile(ROOT/n,root/n)
            rows=[json.loads(x) for x in (ROOT/'data/loops.jsonl').read_text().splitlines()]
            for corrupt in [[rows[0]]*9,[dict(row,extra=1) for row in rows]]:
                (root/'data/loops.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in corrupt))
                p=subprocess.run([sys.executable,'-B','verify_loops.py'],cwd=root,capture_output=True,text=True,timeout=10)
                self.assertNotEqual(p.returncode,0)
if __name__=='__main__':unittest.main(verbosity=2)
