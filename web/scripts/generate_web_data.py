#!/usr/bin/env python3
"""Convert MinimalResolution text tables into browser-loadable data files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def table_kind(path: Path) -> str:
    return "bockstein" if "bocss" in path.name.lower() else "aanss"


def companion_products(path: Path) -> dict[str, str]:
    """Collect multiplication tables belonging to a displayed SS table."""
    name = path.name
    if name.endswith("AANSS_table.txt"):
        prefix, suffixes = name[: -len("AANSS_table.txt")], {
            "a0 (multiplication by 3)": "AANSS_a0.txt",
            "h0": "AANSS_h0.txt",
            "h1": "AANSS_h1.txt",
            "h2": "AANSS_h2.txt",
        }
    elif name.endswith("BocSS_table.txt"):
        prefix, suffixes = name[: -len("BocSS_table.txt")], {
            "a0 (multiplication by 3)": "BocSS_a0.txt",
            "h0": "BocSS_h0.txt",
            "h1": "BocSS_h1.txt",
            "h2": "BocSS_h2.txt",
            **{f"theta{i}": f"BocSS_theta{i}.txt" for i in range(2, 8)},
        }
    else:
        return {}
    products = {}
    for label, suffix in suffixes.items():
        companion = path.with_name(prefix + suffix)
        if companion.is_file():
            products[label] = companion.read_text(encoding="utf-8")
    return products


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate web/data/<table>.js from MinimalResolution tables."
    )
    parser.add_argument("tables", nargs="+", type=Path)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "data",
    )
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    for source in args.tables:
        if not source.is_file():
            parser.error(f"table does not exist: {source}")
        payload = {
            "name": source.name,
            "kind": table_kind(source),
            "text": source.read_text(encoding="utf-8"),
            "products": companion_products(source),
        }
        output = args.output_dir / f"{source.stem}.js"
        output.write_text(
            "globalThis.MINIMALRES_DATA = "
            + json.dumps(payload, ensure_ascii=False, indent=2)
            + ";\n",
            encoding="utf-8",
        )
        print(f"generated {output}")


if __name__ == "__main__":
    main()
