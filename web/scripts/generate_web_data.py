#!/usr/bin/env python3
"""Convert MinimalResolution text tables into browser-loadable data files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def table_kind(path: Path) -> str:
    return "bockstein" if "bocss" in path.name.lower() else "aanss"


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
