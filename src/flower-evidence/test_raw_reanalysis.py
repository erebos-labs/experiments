#!/usr/bin/env python3
import hashlib
import io
import json
import shutil
import tempfile
import importlib.util
import unittest
import sys
import contextlib
import subprocess
from unittest.mock import patch
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw-data"
SCRIPT = ROOT / "raw_reanalysis.py"
EXPECTED_FILES = {
    "exp_Indoor_fall_2016.xlsx",
    "exp_Indoor_spring_2016.xlsx",
    "exp_Outdoor_summer2014_and_exp_Indoor_summer_2015.xlsx",
}


spec = importlib.util.spec_from_file_location("raw_reanalysis", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


@unittest.skipUnless((RAW / "ExpData.zip").is_file(), "Optional verified Dryad archive not supplied in raw-data/")
class RawArchiveTests(unittest.TestCase):
    def test_archive_identity_and_crc(self):
        archive = RAW / "ExpData.zip"
        self.assertEqual(archive.stat().st_size, 69019)
        self.assertEqual(hashlib.md5(archive.read_bytes()).hexdigest(), "a2a2e6a3252b023fe46ef46b507f1145")
        with zipfile.ZipFile(archive) as zipped:
            self.assertEqual(set(zipped.namelist()), EXPECTED_FILES)
            self.assertIsNone(zipped.testzip())

    def test_workbooks_contain_no_active_content(self):
        for path in RAW.glob("*.xlsx"):
            with zipfile.ZipFile(path) as workbook:
                names = workbook.namelist()
                self.assertFalse(any("vbaProject" in name or "externalLinks" in name or "embeddings" in name for name in names))

    def test_record_counts(self):
        counts = {path.name: len(module.records(path)) for path in RAW.glob("*.xlsx")}
        self.assertEqual(counts["exp_Indoor_fall_2016.xlsx"], 298)
        self.assertEqual(counts["exp_Indoor_spring_2016.xlsx"], 112)
        self.assertEqual(counts["exp_Outdoor_summer2014_and_exp_Indoor_summer_2015.xlsx"], 257)

    def test_article_values_and_caption_mismatch(self):
        report = module.raw_summary(sorted(RAW.glob("*.xlsx")))
        checks = report["published_value_checks"]
        self.assertEqual(sum(check["matches_after_rounding"] for check in checks), 5)
        mismatch = report["caption_mismatch"]
        self.assertAlmostEqual(mismatch["raw_high_mean_row_naive_se"][0], 12.2755102)
        self.assertAlmostEqual(mismatch["raw_intermediate_mean_row_naive_se"][0], 12.7745098)
        self.assertEqual(mismatch["caption_counts"], {"Low": 81, "High": 49, "Intermediate": 51})
        self.assertEqual(sum(mismatch["archive_counts"].values()), 298)
        self.assertTrue(all(mismatch["cross_pair_matches_display"].values()))
        self.assertIn("not proof of a label swap", mismatch["interpretation_limit"])

    def test_full_fixture_and_member_binding(self):
        report = module.raw_summary(sorted(RAW.glob("*.xlsx")))
        self.assertEqual(report, json.loads((ROOT / "raw-summary.json").read_text()))
        with tempfile.TemporaryDirectory() as directory:
            dest = Path(directory)
            for name in EXPECTED_FILES | {"ExpData.zip"}:
                shutil.copyfile(RAW / name, dest / name)
            changed = dest / sorted(EXPECTED_FILES)[0]
            changed.write_bytes(changed.read_bytes()[:-1] + b"X")
            with self.assertRaisesRegex(ValueError, "bytes differ"):
                module.raw_summary(sorted(dest.glob("*.xlsx")))

    def test_inspect_uses_bound_bytes_after_path_replacement(self):
        with tempfile.TemporaryDirectory() as d:
            raw=Path(d)
            for name in EXPECTED_FILES | {'ExpData.zip'}:shutil.copyfile(RAW/name,raw/name)
            paths=sorted(raw.glob('*.xlsx'));target=raw/'exp_Indoor_fall_2016.xlsx';spring=raw/'exp_Indoor_spring_2016.xlsx'
            original=module.verified_workbooks
            before=module.inspect(original(paths))[target.name]['rows']
            def interleave(p):
                members=original(p);target.write_bytes(spring.read_bytes());return members
            out=io.StringIO()
            with patch.object(module,'verified_workbooks',interleave),patch.object(sys,'argv',['raw_reanalysis.py','--inspect',*map(str,paths)]),contextlib.redirect_stdout(out):module.main()
            self.assertEqual(json.loads(out.getvalue())[target.name]['rows'],before)

    def test_no_inferential_claim(self):
        report = module.raw_summary(sorted(RAW.glob("*.xlsx")))
        self.assertIn("no independence-assuming p-values", report["kind"])
        self.assertTrue(any("plant identifier" in limit for limit in report["limits"]))


class ParserLimits(unittest.TestCase):
    def test_computed_uncertainty_is_explicitly_row_naive(self):
        result=module.stats([1,3]);self.assertEqual(result['row_naive_se'],1)
        self.assertNotIn('se',result)
    def test_required_data_mode_fails_without_inputs(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for n in ['test_raw_reanalysis.py','raw_reanalysis.py']:shutil.copyfile(ROOT/n,root/n)
            p=subprocess.run([sys.executable,'-B','test_raw_reanalysis.py','--require-data'],cwd=root,capture_output=True,text=True,timeout=10)
            self.assertNotEqual(p.returncode,0);self.assertIn('Required pinned raw data is absent',p.stderr)

    def test_inline_strings_and_oversized_input(self):
        data = io.BytesIO()
        with zipfile.ZipFile(data, "w") as z:
            z.writestr("xl/worksheets/sheet1.xml", '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row><c r="A1" t="inlineStr"><is><t>Group</t></is></c></row></sheetData></worksheet>')
        self.assertEqual(module.read_workbook(io.BytesIO(data.getvalue())), [["Group"]])
        with self.assertRaises(ValueError):
            module.column_index("ZZZZ1")
        huge = io.BytesIO()
        with zipfile.ZipFile(huge, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("xl/worksheets/sheet1.xml", b"X" * (module.MAX_XML_BYTES + 1))
        with self.assertRaisesRegex(ValueError, "Oversized"):
            module.read_workbook(io.BytesIO(huge.getvalue()))

if __name__ == "__main__":
    if "--require-data" in sys.argv:
        sys.argv.remove("--require-data")
        if not (RAW / "ExpData.zip").is_file():
            raise SystemExit("Required pinned raw data is absent; refusing an evidence-validation PASS")
    unittest.main(verbosity=2)
