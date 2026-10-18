#!/usr/bin/env python3
"""Read the verified Dryad XLSX files with the Python standard library only.

The workbooks are ZIP/XML containers. This parser reads cached cell values and
never evaluates formulas, macros, links, or embedded content.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import math
import statistics
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET


NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
CELL_RE = re.compile(r"([A-Z]+)([0-9]+)$")


EXPECTED_FILES = {
    "exp_Indoor_fall_2016.xlsx",
    "exp_Indoor_spring_2016.xlsx",
    "exp_Outdoor_summer2014_and_exp_Indoor_summer_2015.xlsx",
}
ARCHIVE_SHA256 = "2d870d1c4f909c4eda14baf656d46c441a97a738e8b34337604dd775840fe314"
MAX_WORKBOOK_BYTES = 262144
MAX_XML_BYTES = 2097152


def verified_workbooks(paths: list[Path]) -> dict[str, bytes]:
    """Bind every parsed byte to the exact cited archive before attribution."""
    if len(paths) != 3 or {p.name for p in paths} != EXPECTED_FILES:
        raise ValueError("Supply exactly the three cited workbook members")
    parent = paths[0].resolve().parent
    if any(p.resolve().parent != parent for p in paths):
        raise ValueError("Workbooks must share the directory containing ExpData.zip")
    archive = parent / "ExpData.zip"
    if archive.stat().st_size != 69019:
        raise ValueError("The cited archive must contain exactly 69019 bytes")
    payload = archive.read_bytes()
    if hashlib.sha256(payload).hexdigest() != ARCHIVE_SHA256:
        raise ValueError("Archive SHA-256 differs from the verified source")
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        if len(z.infolist()) != 3 or set(z.namelist()) != EXPECTED_FILES:
            raise ValueError("Unexpected source archive members")
        members = {}
        for p in paths:
            info = z.getinfo(p.name)
            if not 0 < info.file_size <= MAX_WORKBOOK_BYTES or p.stat().st_size != info.file_size:
                raise ValueError("Workbook size differs from its bounded source member")
            data = z.read(p.name)
            if p.read_bytes() != data:
                raise ValueError("Unpacked workbook bytes differ from the cited archive")
            members[p.name] = data
    return members


def bounded_member(archive: zipfile.ZipFile, name: str) -> bytes:
    info = archive.getinfo(name)
    if info.file_size > MAX_XML_BYTES:
        raise ValueError("XML entry exceeds the supported source limit")
    data = archive.read(name)
    if b"<!DOCTYPE" in data.upper() or b"<!ENTITY" in data.upper():
        raise ValueError("Document types and entities are unsupported")
    return data


def column_index(reference: str) -> int:
    match = CELL_RE.match(reference)
    if not match:
        raise ValueError(f"unexpected cell reference: {reference}")
    if len(match.group(1)) > 2:
        raise ValueError("Column exceeds supported workbook width")
    index = 0
    for letter in match.group(1):
        index = index * 26 + ord(letter) - 64
    if index > 64:
        raise ValueError("Column exceeds supported workbook width")
    return index - 1


def shared_strings(archive: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []
    root = ET.fromstring(bounded_member(archive, "xl/sharedStrings.xml"))
    return ["".join(node.text or "" for node in item.iter(NS + "t")) for item in root]


def read_workbook(path: Path) -> list[list[object | None]]:
    if isinstance(path, Path):
        if path.stat().st_size > MAX_WORKBOOK_BYTES:
            raise ValueError("Workbook exceeds supported compressed size")
        path = io.BytesIO(path.read_bytes())
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        if len(infos) > 64 or sum(i.file_size for i in infos) > 8388608:
            raise ValueError("Workbook container exceeds supported limits")
        if any(i.file_size > MAX_XML_BYTES or i.flag_bits & 1 for i in infos):
            raise ValueError("Oversized or encrypted workbook entry")
        strings = shared_strings(archive)
        root = ET.fromstring(bounded_member(archive, "xl/worksheets/sheet1.xml"))
        rows: list[list[object | None]] = []
        for row_node in root.iter(NS + "row"):
            if len(rows) >= 2000:
                raise ValueError("Row count exceeds supported source limit")
            values: dict[int, object | None] = {}
            cells = row_node.findall(NS + "c")
            if len(cells) > 64:
                raise ValueError("Cell count exceeds supported row width")
            for cell in cells:
                index = column_index(cell.attrib["r"])
                kind = cell.attrib.get("t")
                value_node = cell.find(NS + "v")
                raw = None if value_node is None else value_node.text
                if kind == "inlineStr":
                    value: object | None = "".join(node.text or "" for node in cell.iter(NS + "t"))
                elif raw is None:
                    value = None
                elif kind == "s":
                    value = strings[int(raw)]
                elif kind == "b":
                    value = raw == "1"
                elif kind in {"str", "inlineStr"}:
                    value = raw
                else:
                    try:
                        number = float(raw)
                        value = int(number) if number.is_integer() else number
                    except ValueError:
                        value = raw
                values[index] = value
            width = max(values, default=-1) + 1
            rows.append([values.get(i) for i in range(width)])
        return rows


def pad(row: list[object | None], width: int) -> list[object | None]:
    return row + [None] * (width - len(row))


def inspect(members: dict[str, bytes]) -> dict[str, object]:
    report: dict[str, object] = {}
    for name, data in members.items():
        rows = read_workbook(io.BytesIO(data))
        width = max(map(len, rows), default=0)
        report[name] = {
            "rows": len(rows),
            "columns": width,
            "preview": [pad(row, width) for row in rows[:12]],
        }
    return report


def records(path: Path) -> list[dict[str, object | None]]:
    rows = read_workbook(path)
    headers = [str(value) if value is not None else "" for value in rows[0]]
    usable = [(index, header) for index, header in enumerate(headers) if header]
    output = []
    for row in rows[1:]:
        item = {header: (row[index] if index < len(row) else None) for index, header in usable}
        if item.get("Group") is not None:
            output.append(item)
    return output


def stats(values: list[object | None]) -> dict[str, float | int | None]:
    numbers = [float(value) for value in values if isinstance(value, (int, float))]
    if not numbers:
        return {"n": 0, "mean": None, "median": None, "row_naive_se": None}
    return {
        "n": len(numbers),
        "mean": round(statistics.fmean(numbers), 8),
        "median": round(statistics.median(numbers), 8),
        "row_naive_se": round(statistics.stdev(numbers) / math.sqrt(len(numbers)), 8) if len(numbers) > 1 else None,
    }


def truncate(value: float, digits: int) -> float:
    """Match the apparent toward-zero display convention in the captions."""
    scale = 10 ** digits
    return math.trunc(value * scale) / scale


OUTCOMES = ("TotVOL1", "SugCon1", "SugAmount1", "TotVOL2", "SugCon2", "SugAmount2")


def summarize_groups(rows: list[dict[str, object | None]]) -> dict[str, object]:
    groups: dict[str, list[dict[str, object | None]]] = defaultdict(list)
    for row in rows:
        groups[str(row["Group"])].append(row)
    return {
        group: {
            "rows": len(members),
            "outcomes": {outcome: stats([member.get(outcome) for member in members]) for outcome in OUTCOMES},
        }
        for group, members in sorted(groups.items())
    }


def difference(groups: dict[str, object], left: str, right: str, outcome: str) -> dict[str, object]:
    left_mean = groups[left]["outcomes"][outcome]["mean"]  # type: ignore[index]
    right_mean = groups[right]["outcomes"][outcome]["mean"]  # type: ignore[index]
    absolute = float(left_mean) - float(right_mean)
    relative = absolute / float(right_mean) * 100 if float(right_mean) else None
    return {
        "left": left,
        "right": right,
        "outcome": outcome,
        "mean_difference": round(absolute, 8),
        "relative_percent": None if relative is None else round(relative, 4),
    }


def raw_summary(paths: list[Path]) -> dict[str, object]:
    members = verified_workbooks(paths)
    by_name = {name: records(io.BytesIO(data)) for name, data in members.items()}
    summer = by_name["exp_Outdoor_summer2014_and_exp_Indoor_summer_2015.xlsx"]
    cohorts = {
        "summer_2014_outdoor_1a": [row for row in summer if row.get("Exp") == "1a"],
        "summer_2015_indoor_1b": [row for row in summer if row.get("Exp") == "1b"],
        "summer_2014_2015_combined": summer,
        "fall_2016_indoor": by_name["exp_Indoor_fall_2016.xlsx"],
        "spring_2016_indoor": by_name["exp_Indoor_spring_2016.xlsx"],
    }
    summaries = {name: summarize_groups(rows) for name, rows in cohorts.items()}
    comparisons = {
        "summer_combined_low_vs_high": [
            difference(summaries["summer_2014_2015_combined"], "Low", "High", outcome)
            for outcome in ("SugCon2", "TotVOL2", "SugAmount2")
        ],
        "summer_combined_low_vs_silent": [
            difference(summaries["summer_2014_2015_combined"], "Low", "Silent", outcome)
            for outcome in ("SugCon2", "TotVOL2", "SugAmount2")
        ],
        "summer_combined_bee_vs_silent": [
            difference(summaries["summer_2014_2015_combined"], "Bee", "Silent", outcome)
            for outcome in ("SugCon2", "TotVOL2", "SugAmount2")
        ],
        "fall_low_vs_high": [
            difference(summaries["fall_2016_indoor"], "Low", "High", outcome)
            for outcome in ("SugCon2", "TotVOL2", "SugAmount2")
        ],
        "fall_low_vs_intermediate": [
            difference(summaries["fall_2016_indoor"], "Low", "Intermediate", outcome)
            for outcome in ("SugCon2", "TotVOL2", "SugAmount2")
        ],
        "fall_low_vs_low_in_jar": [
            difference(summaries["fall_2016_indoor"], "Low", "Low in Jar", outcome)
            for outcome in ("SugCon2", "TotVOL2", "SugAmount2")
        ],
        "spring_low_vs_high": [
            difference(summaries["spring_2016_indoor"], "Low", "High", outcome)
            for outcome in ("SugCon2", "TotVOL2", "SugAmount2")
        ],
    }

    # Parser/data sanity checks against values printed in the original article.
    expected = {
        ("summer_2014_2015_combined", "Low"): 19.8,
        ("summer_2014_2015_combined", "Bee"): 19.1,
        ("summer_2014_2015_combined", "Silent"): 16.3,
        ("summer_2014_2015_combined", "High"): 16.0,
        ("fall_2016_indoor", "Low"): 15.9,
        ("fall_2016_indoor", "High"): 12.8,
        ("fall_2016_indoor", "Intermediate"): 12.3,
    }
    checks = []
    for (cohort, group), published in expected.items():
        observed = summaries[cohort][group]["outcomes"]["SugCon2"]["mean"]  # type: ignore[index]
        checks.append({
            "cohort": cohort,
            "group": group,
            "raw_mean": observed,
            "published_one_decimal": published,
            "matches_after_rounding": round(float(observed), 1) == published,
        })
    fall_high = summaries["fall_2016_indoor"]["High"]["outcomes"]["SugCon2"]  # type: ignore[index]
    fall_intermediate = summaries["fall_2016_indoor"]["Intermediate"]["outcomes"]["SugCon2"]  # type: ignore[index]
    caption_mismatch = {
        "observation": "The deposited fall-2016 High and Intermediate numerical pairs cross-match the article's Figure 2 caption at its displayed precision.",
        "raw_high_mean_row_naive_se": [fall_high["mean"], fall_high["row_naive_se"]],
        "raw_intermediate_mean_row_naive_se": [fall_intermediate["mean"], fall_intermediate["row_naive_se"]],
        "caption_high_mean_se": [12.8, 0.7],
        "caption_intermediate_mean_se": [12.3, 0.77],
        "caption_counts": {"Low": 81, "High": 49, "Intermediate": 51},
        "archive_counts": {
            "Low": summaries["fall_2016_indoor"]["Low"]["rows"],
            "High": summaries["fall_2016_indoor"]["High"]["rows"],
            "Intermediate": summaries["fall_2016_indoor"]["Intermediate"]["rows"],
            "Low in Jar": summaries["fall_2016_indoor"]["Low in Jar"]["rows"],
            "High in Jar": summaries["fall_2016_indoor"]["High in Jar"]["rows"],
        },
        "cross_pair_matches_display": {
            "raw_high_to_caption_intermediate": (
                round(float(fall_high["mean"]), 1) == 12.3
                and truncate(float(fall_high["row_naive_se"]), 2) == 0.77
            ),
            "raw_intermediate_to_caption_high": (
                round(float(fall_intermediate["mean"]), 1) == 12.8
                and truncate(float(fall_intermediate["row_naive_se"]), 1) == 0.7
            ),
        },
        "se_display_note": "The caption's SE digits are consistent with truncation toward zero at the shown precision, not conventional rounding. The article does not state that display convention.",
        "interpretation_limit": "This is a descriptive provenance mismatch, not proof of a label swap. The available record does not identify whether the caption, the deposited treatment labels, or an upstream export is wrong.",
    }

    return {
        "kind": "descriptive raw-data reanalysis; no independence-assuming p-values",
        "source_archive": {
            "doi": "10.5061/dryad.6n5h0pb",
            "bytes": 69019,
            "md5": "a2a2e6a3252b023fe46ef46b507f1145",
            "sha256": ARCHIVE_SHA256,
            "parsed_bytes_bound_to_archive": True,
        },
        "limits": [
            "The spreadsheets contain no stable plant identifier, so rows cannot safely be treated as independent plants for new hypothesis tests.",
            "Means, medians, row-naive s/sqrt(row count), and unadjusted descriptive contrasts are reported. Clustering and repeated-measure effects are unknown; row-naive values are not independent-plant uncertainty estimates. No p-values are recomputed.",
            "SugAmount fields are the deposited density-corrected sugar-mass values; formulas are not re-evaluated.",
            "The original article and the 2020 critique used different inferential models; this summary does not adjudicate those models.",
        ],
        "published_value_checks": checks,
        "caption_mismatch": caption_mismatch,
        "cohorts": summaries,
        "descriptive_contrasts": comparisons,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--inspect", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = inspect(verified_workbooks(args.paths)) if args.inspect else raw_summary(args.paths)
    payload = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.out:
        args.out.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")


if __name__ == "__main__":
    main()
