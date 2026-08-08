#!/usr/bin/env python3
"""Extract a one-copy ANSS E2 basis for M(3) from Eva Belmont's Bockstein table.

The raw BPBocSS table contains the Bockstein E0 computation.  Its d0 pairs
cancel before E1, and the target of a positive Bockstein differential is a
3-adically filtered copy of a bottom-cell class rather than another underlying
M(3) generator.  Consequently a one-copy basis consists of:

* every untagged (permanent) entry, as a bottom-cell class; and
* the right-hand source of every d_r with r > 0, as a top-cell class.

The printed Bockstein degree is N = 2D-k, where k is the resolution degree and
D is the internal degree.  This script converts it to the usual
(stem, ANSS filtration) coordinates before writing browser data.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


DEGREE_RE = re.compile(r"\|deg=(-?\d+)")
DIFFERENTIAL_RE = re.compile(r"\|d(\d+)")
FILTRATION_RE = re.compile(r"\[(-?\d+)-")
DEFAULT_SOURCE_URL = (
    "https://github.com/ebelmont/ANSS_data/blob/master/data/"
    "185_BPBocSS_table.txt"
)
OPERATIONS = (
    ("h0 (alpha1 on M3)", "BPBocSS_h0.txt", (3, 1)),
    ("theta2 (boundary beta1)", "BPBocSS_theta2.txt", (11, 1)),
    ("theta3 (boundary beta2)", "BPBocSS_theta3.txt", (27, 1)),
    ("theta4 (boundary beta3/3)", "BPBocSS_theta4.txt", (35, 1)),
    ("theta5 (boundary beta4)", "BPBocSS_theta5.txt", (59, 1)),
    ("theta6 (boundary beta5)", "BPBocSS_theta6.txt", (75, 1)),
    ("theta7 (boundary beta6/3)", "BPBocSS_theta7.txt", (83, 1)),
)


@dataclass(frozen=True)
class MooreClass:
    name: str
    stem: int
    filtration: int
    cell: str
    bockstein_length: int | None
    target: str | None

    def table_line(self) -> str:
        details = [f"cell={self.cell}"]
        if self.bockstein_length is not None:
            details.append(f"bockstein=d{self.bockstein_length}")
        if self.target is not None:
            details.append(f"target={self.target}")
        suffix = "\t|" + "\t|".join(details)
        return (
            f"{self.name}\t|deg=({self.stem},{self.filtration})"
            f"{suffix}"
        )


def filtration(name: str, *, line_number: int) -> int:
    match = FILTRATION_RE.search(name)
    if match is None:
        raise ValueError(
            f"line {line_number}: cannot read resolution filtration from {name!r}"
        )
    return int(match.group(1))


def stem_from_target_degree(
    printed_degree: int, target_filtration: int, *, line_number: int
) -> int:
    numerator = printed_degree - target_filtration
    if numerator % 2:
        raise ValueError(
            f"line {line_number}: degree {printed_degree} and filtration "
            f"{target_filtration} have inconsistent parity"
        )
    return numerator // 2


def extract_moore_classes(text: str) -> tuple[list[MooreClass], Counter[str]]:
    classes: list[MooreClass] = []
    counts: Counter[str] = Counter()
    seen: dict[str, MooreClass] = {}

    def add(item: MooreClass, *, line_number: int) -> None:
        previous = seen.get(item.name)
        if previous is not None:
            raise ValueError(
                f"line {line_number}: duplicate Moore generator {item.name!r}; "
                f"previously read as {previous}"
            )
        seen[item.name] = item
        classes.append(item)

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        raw = raw_line.strip()
        if not raw:
            continue
        degree_match = DEGREE_RE.search(raw)
        if degree_match is None:
            raise ValueError(f"line {line_number}: missing |deg=N field")
        printed_degree = int(degree_match.group(1))

        if "<-" not in raw:
            name = raw.split("|", 1)[0].strip()
            filt = filtration(name, line_number=line_number)
            stem = stem_from_target_degree(
                printed_degree, filt, line_number=line_number
            )
            add(
                MooreClass(name, stem, filt, "bottom", None, None),
                line_number=line_number,
            )
            counts["bottom"] += 1
            continue

        target_part, source_part = raw.split("<-", 1)
        target = target_part.strip()
        source = source_part.split("|", 1)[0].strip()
        differential_match = DIFFERENTIAL_RE.search(raw)
        if differential_match is None:
            raise ValueError(f"line {line_number}: arrow has no |dR field")
        length = int(differential_match.group(1))
        target_filtration = filtration(target, line_number=line_number)
        source_filtration = filtration(source, line_number=line_number)
        if target_filtration != source_filtration + 1:
            raise ValueError(
                f"line {line_number}: expected adjacent ANSS filtrations, got "
                f"target {target_filtration} and source {source_filtration}"
            )
        target_stem = stem_from_target_degree(
            printed_degree, target_filtration, line_number=line_number
        )

        if length == 0:
            counts["d0_pairs"] += 1
            continue

        add(
            MooreClass(
                source,
                target_stem + 1,
                source_filtration,
                "top",
                length,
                target,
            ),
            line_number=line_number,
        )
        counts["top"] += 1
        counts[f"d{length}_sources"] += 1

    counts["classes"] = len(classes)
    return classes, counts


def default_output_name(source: Path) -> str:
    suffix = "_BPBocSS_table"
    prefix = source.stem[: -len(suffix)] if source.stem.endswith(suffix) else source.stem
    return f"{prefix}_M3_ANSS_E2.js"


def normalize_product_table(
    text: str,
    basis: dict[str, MooreClass],
    shift: tuple[int, int],
    *,
    table_name: str,
) -> tuple[str, dict[str, int]]:
    """Restrict a raw Bockstein operation to the one-copy M(3) basis."""
    output_lines: list[str] = []
    selected_sources: set[str] = set()
    nonzero_rows = 0
    distinct_targets = 0
    coefficient_two_targets = 0

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        raw = raw_line.strip()
        if not raw:
            continue
        parts = re.split(r"\s*->\s*", raw, maxsplit=1)
        if len(parts) != 2:
            raise ValueError(f"{table_name} line {line_number}: missing ->")
        source, rhs = parts
        if source not in basis:
            continue
        if source in selected_sources:
            raise ValueError(
                f"{table_name} line {line_number}: duplicate basis source {source!r}"
            )
        selected_sources.add(source)

        multiplicities: Counter[str] = Counter(
            term.strip()
            for term in rhs.split("+")
            if term.strip() and term.strip() != "o"
        )
        normalized_targets: list[str] = []
        source_class = basis[source]
        for target, multiplicity in multiplicities.items():
            coefficient = multiplicity % 3
            if coefficient == 0:
                continue
            if target not in basis:
                raise ValueError(
                    f"{table_name} line {line_number}: nonzero target {target!r} "
                    "is not in the one-copy M(3) basis"
                )
            target_class = basis[target]
            actual_shift = (
                target_class.stem - source_class.stem,
                target_class.filtration - source_class.filtration,
            )
            if actual_shift != shift:
                raise ValueError(
                    f"{table_name} line {line_number}: {source!r} -> {target!r} "
                    f"has shift {actual_shift}, expected {shift}"
                )
            normalized_targets.extend([target] * coefficient)
            distinct_targets += 1
            if coefficient == 2:
                coefficient_two_targets += 1

        if normalized_targets:
            nonzero_rows += 1
            output_lines.append(f"{source}\t->\t{'+'.join(normalized_targets)}")

    missing_sources = set(basis).difference(selected_sources)
    extra_count = len(selected_sources) - len(basis)
    if missing_sources or extra_count:
        preview = ", ".join(sorted(missing_sources)[:5])
        raise ValueError(
            f"{table_name}: expected one row for each of {len(basis)} basis "
            f"sources; missing {len(missing_sources)} ({preview})"
        )

    stats = {
        "source_rows": len(selected_sources),
        "nonzero_rows": nonzero_rows,
        "distinct_targets": distinct_targets,
        "coefficient_two_targets": coefficient_two_targets,
    }
    text_output = "\n".join(output_lines)
    return (text_output + "\n" if text_output else ""), stats


def normalized_products(
    table: Path, classes: list[MooreClass]
) -> tuple[dict[str, str], dict[str, dict[str, int]]]:
    suffix = "BPBocSS_table.txt"
    if not table.name.endswith(suffix):
        return {}, {}
    prefix = table.name[: -len(suffix)]
    basis = {item.name: item for item in classes}
    products: dict[str, str] = {}
    stats: dict[str, dict[str, int]] = {}
    for label, companion_suffix, shift in OPERATIONS:
        companion = table.with_name(prefix + companion_suffix)
        if not companion.is_file():
            continue
        products[label], stats[label] = normalize_product_table(
            companion.read_text(encoding="utf-8"),
            basis,
            shift,
            table_name=companion.name,
        )
    return products, stats


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a one-copy E2_ANSS(M3) web dataset from BPBocSS data."
    )
    parser.add_argument("table", type=Path)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "data",
    )
    parser.add_argument("--source-url", default=DEFAULT_SOURCE_URL)
    args = parser.parse_args()

    if not args.table.is_file():
        parser.error(f"table does not exist: {args.table}")

    classes, counts = extract_moore_classes(args.table.read_text(encoding="utf-8"))
    if not classes:
        parser.error("table produced no M(3) classes")

    products, operation_counts = normalized_products(args.table, classes)
    payload = {
        "name": f"{args.table.stem.replace('_BPBocSS_table', '')} M3 ANSS E2",
        "kind": "m3",
        "description": (
            "One-copy additive basis of E2_ANSS(M3), extracted after discarding "
            "Bockstein d0 pairs and repeated 3-adic target representatives."
        ),
        "source": args.source_url,
        "counts": dict(counts),
        "operation_counts": operation_counts,
        "text": "\n".join(item.table_line() for item in classes) + "\n",
        "products": products,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / default_output_name(args.table)
    output.write_text(
        "globalThis.MINIMALRES_DATA = "
        + json.dumps(payload, ensure_ascii=False, indent=2)
        + ";\n",
        encoding="utf-8",
    )

    differential_summary = ", ".join(
        f"{key}={counts[key]}"
        for key in sorted(counts)
        if key.startswith("d") and key.endswith("_sources")
    )
    print(
        f"generated {output}: {counts['classes']} classes "
        f"({counts['bottom']} bottom, {counts['top']} top; "
        f"discarded {counts['d0_pairs']} d0 pairs; {differential_summary})"
    )
    if products:
        print(
            "normalized operations: "
            + ", ".join(
                f"{label.split(' ', 1)[0]}={operation_counts[label]['nonzero_rows']}"
                for label in products
            )
            + " nonzero source rows"
        )


if __name__ == "__main__":
    main()
