#!/usr/bin/env python3
from __future__ import annotations

import json
from html.parser import HTMLParser
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import analyze


HERE = Path(__file__).resolve().parent
ROOT = HERE
ARTIFACT = ROOT / "index.html"
SUMMARY = ROOT / "summary.json"


class SummaryTests(unittest.TestCase):
    def test_published_contrasts(self) -> None:
        summary = analyze.build_summary()
        self.assertEqual(
            summary["contrasts"]["exp1_low_minus_silence"]["percentage_point_difference"],
            3.5,
        )
        self.assertEqual(
            summary["contrasts"]["exp1_bee_minus_silence"]["percentage_point_difference"],
            2.8,
        )
        self.assertAlmostEqual(
            summary["counterfactual_endpoint_demo"]["proxy_relative_percent"],
            -0.39,
            places=2,
        )
        self.assertAlmostEqual(
            summary["counterfactual_endpoint_demo"]["flat_proxy_treatment_volume_ul"],
            0.82323,
            places=5,
        )

    def test_saved_summary_matches_generator(self) -> None:
        self.assertEqual(json.loads(SUMMARY.read_text()), analyze.build_summary())
        self.assertEqual(SUMMARY.read_bytes(), (json.dumps(analyze.build_summary(), indent=2, sort_keys=True) + "\n").encode("utf-8"))


class ArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.html = ARTIFACT.read_text(encoding="utf-8")

    def test_is_standalone_and_has_primary_sources(self) -> None:
        self.assertIn("<!doctype html>", self.html.lower())
        self.assertNotIn("<script src=", self.html.lower())
        self.assertNotIn("<link rel=\"stylesheet\"", self.html.lower())
        for url in analyze.SOURCES.values():
            self.assertIn(url, self.html)

    def test_interactions_and_caveats_present(self) -> None:
        for marker in (
            "dataset-select",
            "stimulus-controls",
            "after-volume",
            "evidence-ladder",
            "Untested gulf",
            "not a replication",
            "Caption/data mismatch",
            "This does not prove which labels are wrong",
            "archive identity verified",
        ):
            self.assertIn(marker, self.html)

    def test_no_network_or_storage_calls(self) -> None:
        for forbidden in ("fetch(", "XMLHttpRequest", "WebSocket", "localStorage", "sessionStorage", "sendBeacon", "EventSource", "indexedDB", "serviceWorker", "new Worker"):
            self.assertNotIn(forbidden, self.html)

    def test_no_remote_resource_attributes_or_css_urls(self):
        class Resources(HTMLParser):
            def __init__(self):super().__init__();self.bad=[]
            def handle_starttag(self, tag, attrs):
                values=dict(attrs)
                if tag in {"form","iframe","object","embed"}:self.bad.append(tag)
                for name in ("src","srcset","poster","action","formaction"):
                    if name in values:self.bad.append(name)
                if tag=="link" and values.get("rel") in {"stylesheet","preload","prefetch"}:self.bad.append(tag)
        parser=Resources();parser.feed(self.html)
        self.assertEqual(parser.bad,[])
        self.assertNotRegex(self.html,r"(?i)(?:url\s*\(|@import)")

    def test_embedded_group_values_match_summary_generator(self) -> None:
        block = re.search(r"const datasets = (.*?);\s*const select", self.html, re.S)
        self.assertIsNotNone(block)
        code = "const vm=require('node:vm');const fs=require('node:fs');console.log(JSON.stringify(vm.runInNewContext('('+fs.readFileSync(0,'utf8')+')',{},{timeout:500})))"
        cp = subprocess.run(["node", "-e", code], input=block.group(1), capture_output=True, text=True, timeout=3)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        actual = json.loads(cp.stdout)
        for panel, name in [("exp1", "combined_2014_2015"), ("exp2", "fall_2016")]:
            expected = analyze.EXPERIMENTS[name]["groups"]
            self.assertEqual(len(actual[panel]["groups"]), len(expected))
            for group in actual[panel]["groups"]:
                values = expected[group["name"]]
                self.assertEqual((group["mean"], group["se"], group["n"]), (values["mean_brix_pct"], values["se"], values["n"]))

    def test_inline_javascript_syntax(self) -> None:
        scripts = re.findall(r"<script>(.*?)</script>", self.html, flags=re.S)
        self.assertEqual(len(scripts), 1)
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as handle:
            handle.write(scripts[0])
            script_path = handle.name
        try:
            completed = subprocess.run(
                ["node", "--check", script_path], capture_output=True, text=True
            )
        except FileNotFoundError:
            self.skipTest("node unavailable")
        self.assertEqual(completed.returncode, 0, completed.stderr)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
