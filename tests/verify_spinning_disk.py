#!/usr/bin/env python3
"""Bounded reproducibility and package checks for the spinning-disk module."""

from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "src" / "spinning-disk"


def run(name: str) -> None:
    completed = subprocess.run(
        [sys.executable, "-B", str(MODULE / name), "--check"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "PASS" in completed.stdout, name


for script in (
    "model.py",
    "fit_sensitivity.py",
    "identifiability.py",
    "mixed_window_fit.py",
    "candidate_selection.py",
):
    run(script)

source = MODULE / "index.html"
built = ROOT / "docs" / "spinning-disk" / "index.html"
assert source.read_bytes() == built.read_bytes()
text = source.read_text(encoding="utf-8")
assert 'meta name="referrer" content="no-referrer"' in text
assert "Synthetic demonstration only" in text
assert "not a contact-dynamics simulation" in text
for token in (
    "fetch(", "XMLHttpRequest", "sendBeacon", "WebSocket", "EventSource",
    "serviceWorker", "localStorage", "sessionStorage", "indexedDB", "document.cookie",
):
    assert token not in text, token


def is_remote(value: str) -> bool:
    value = value.strip().lower()
    return value.startswith(("http://", "https://", "//"))


class RequestSurfaceScanner(HTMLParser):
    """Reject remote fetch surfaces while permitting ordinary citation anchors."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.problems: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {name.lower(): (value or "") for name, value in attrs}
        tag = tag.lower()

        for name in ("src", "poster", "background"):
            if is_remote(values.get(name, "")):
                self.problems.append(f"remote {tag}[{name}]")

        if "srcset" in values:
            candidates = [item.strip().split()[0] for item in values["srcset"].split(",") if item.strip()]
            if any(is_remote(candidate) for candidate in candidates):
                self.problems.append(f"remote {tag}[srcset]")

        if tag == "object" and is_remote(values.get("data", "")):
            self.problems.append("remote object[data]")
        if tag in {"link", "base", "use", "image", "feimage"} and is_remote(values.get("href", values.get("xlink:href", ""))):
            self.problems.append(f"remote svg {tag}[href]")
        if tag in {"form", "button", "input"}:
            for name in ("action", "formaction"):
                if is_remote(values.get(name, "")):
                    self.problems.append(f"remote {tag}[{name}]")
        if tag == "html" and is_remote(values.get("manifest", "")):
            self.problems.append("remote html[manifest]")
        if tag in {"a", "area"} and any(is_remote(item) for item in values.get("ping", "").split()):
            self.problems.append(f"remote {tag}[ping]")
        if tag == "meta" and values.get("http-equiv", "").strip().lower() == "refresh":
            if re.search(r"(?:^|;)\s*url\s*=\s*(?:https?:)?//", values.get("content", ""), re.IGNORECASE):
                self.problems.append("remote meta refresh")


scanner = RequestSurfaceScanner()
scanner.feed(text)
assert not scanner.problems, scanner.problems

for remote_fixture in (
    '<img src="https://example.invalid/a.png">',
    '<source srcset="local.png 1x, //example.invalid/a.png 2x">',
    '<object data="https://example.invalid/a.bin"></object>',
    '<link rel="stylesheet" href="https://example.invalid/a.css">',
    '<base href="https://example.invalid/">',
    '<svg><use href="https://example.invalid/a.svg#x"></use></svg>',
    '<meta http-equiv="refresh" content="0; URL=https://example.invalid/">',
    '<a href="https://citation.invalid/" ping="https://example.invalid/p">citation</a>',
    '<html manifest="https://example.invalid/a.appcache">',
):
    fixture_scanner = RequestSurfaceScanner()
    fixture_scanner.feed(remote_fixture)
    assert fixture_scanner.problems, remote_fixture

# Ordinary outbound citation anchors are intentional and must not be confused
# with automatic page-load or tracking requests.
citation_scanner = RequestSurfaceScanner()
citation_scanner.feed('<a href="https://example.invalid/paper">paper</a>')
assert not citation_scanner.problems
assert not re.search(r"@import\s+(?:url\()?\s*['\"]?(?:https?:)?//", text, re.IGNORECASE)
assert not re.search(r"url\(\s*['\"]?(?:https?:)?//", text, re.IGNORECASE)
print(
    "PASS spinning disk: five bounded standard-library model checks; "
    "source/build byte equality; limitations and referrer policy; named script network, "
    "storage, cookie, worker and event-stream sinks absent; structural HTML/CSS remote-request "
    "surfaces absent (ordinary citation anchors permitted)"
)
print("page_sha256", hashlib.sha256(source.read_bytes()).hexdigest())
