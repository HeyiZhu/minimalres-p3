#!/usr/bin/env python3
"""Convert MinimalResolution text tables into browser-loadable data files."""

from __future__ import annotations

import argparse
import json
import re
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


def parse_product_table(text: str) -> dict[str, dict[str, int]]:
    result = {}
    for row in text.splitlines():
        if "->" not in row:
            continue
        source, target_text = map(str.strip, row.split("->", 1))
        targets = {}
        for target in (x.strip() for x in target_text.split("+")):
            if target and target != "o":
                targets[target] = (targets.get(target, 0) + 1) % 3
        result[source] = {name: coefficient for name, coefficient in targets.items() if coefficient}
    return result


def rref(matrix: list[list[int]]) -> tuple[list[list[int]], list[int]]:
    a = [[x % 3 for x in row] for row in matrix]
    if not a:
        return a, []
    rows, cols, pivot_row, pivots = len(a), len(a[0]), 0, []
    for col in range(cols):
        pivot = next((i for i in range(pivot_row, rows) if a[i][col]), None)
        if pivot is None:
            continue
        a[pivot_row], a[pivot] = a[pivot], a[pivot_row]
        inverse = 1 if a[pivot_row][col] == 1 else 2
        a[pivot_row] = [(inverse * x) % 3 for x in a[pivot_row]]
        for i in range(rows):
            if i != pivot_row and a[i][col]:
                factor = a[i][col]
                a[i] = [(x - factor * y) % 3 for x, y in zip(a[i], a[pivot_row])]
        pivots.append(col)
        pivot_row += 1
        if pivot_row == rows:
            break
    return a, pivots


def nullspace(matrix: list[list[int]], width: int) -> list[list[int]]:
    reduced, pivots = rref(matrix)
    free = [j for j in range(width) if j not in pivots]
    basis = []
    for free_col in free:
        vector = [0] * width
        vector[free_col] = 1
        for row, pivot in enumerate(pivots):
            vector[pivot] = (-reduced[row][free_col]) % 3
        basis.append(vector)
    return basis


def solve_in_basis(vector: list[int], basis: list[list[int]]) -> list[int] | None:
    if not basis:
        return [] if not any(vector) else None
    equations = [[basis[j][i] for j in range(len(basis))] + [vector[i]] for i in range(len(vector))]
    reduced, pivots = rref(equations)
    variables = len(basis)
    if any(not any(row[:variables]) and row[variables] for row in reduced):
        return None
    answer = [0] * variables
    for row, pivot in enumerate(pivots):
        if pivot < variables:
            answer[pivot] = reduced[row][variables]
    return answer


def table_basis(table_text: str) -> tuple[list[str], dict[str, tuple[int, int]]]:
    names, degrees = [], {}
    for row in table_text.splitlines():
        if "<-" in row:
            continue
        degree = re.search(r"\|deg=\((-?\d+),(-?\d+)\)", row)
        if not degree:
            continue
        name = row.split("|", 1)[0].strip()
        names.append(name)
        degrees[name] = tuple(map(int, degree.groups()))
    return names, degrees


def prefixed_products(text: str, prefix: str) -> str:
    rows = []
    for source, targets in parse_product_table(text).items():
        if targets:
            rhs = []
            for target, coefficient in targets.items():
                rhs.extend([f"{prefix}·{target}"] * coefficient)
            rows.append(f"{prefix}·{source}\t->\t" + "+".join(rhs) + "+o")
    return "\n".join(rows) + ("\n" if rows else "")


def calpha1_payloads(source: Path, table_text: str, products: dict[str, str]) -> tuple[dict, dict] | None:
    """Build C(alpha_1) AHSS E1 and its d1-homology (AHSS E2)."""
    h0 = products.get("h0")
    if not h0 or "AANSS_table" not in source.name:
        return None
    rows = []
    names = set()
    for row in table_text.splitlines():
        degree = re.search(r"\|deg=\((-?\d+),(-?\d+)\)", row)
        if not degree:
            continue
        x, y = map(int, degree.groups())
        relation = row.split("|", 1)[0].strip()
        suffix = row[row.find("|d") : row.find("|deg=")].strip() if "|d" in row else ""
        if "<-" in relation:
            target, origin = map(str.strip, relation.split("<-", 1))
            names.update((target, origin))
            rows.append(f"bottom·{target}\t<-\tbottom·{origin}\t{suffix}\t|deg=({x},{y})\t|cell=bottom")
            rows.append(f"top·{target}\t<-\ttop·{origin}\t{suffix}\t|deg=({x + 4},{y})\t|cell=top")
        else:
            names.add(relation)
            rows.append(f"bottom·{relation}\t|deg=({x},{y})\t|cell=bottom")
            rows.append(f"top·{relation}\t|deg=({x + 4},{y})\t|cell=top")
    attaching = []
    for row in h0.splitlines():
        if "->" not in row:
            continue
        origin, result = map(str.strip, row.split("->", 1))
        targets = list(dict.fromkeys(x.strip() for x in result.split("+") if x.strip() != "o"))
        if origin in names:
            visible = [f"bottom·{target}" for target in targets if target in names]
            if visible:
                attaching.append(f"top·{origin}\t->\t" + "+".join(visible) + "+o")
    ahss_products = {"AHSS d1 = alpha1 = h0": "\n".join(attaching) + "\n"}
    for label, text in products.items():
        ahss_products[f"{label} on both cells"] = prefixed_products(text, "bottom") + prefixed_products(text, "top")
    base = source.name.replace("AANSS_table.txt", "CAlpha1")
    ahss = {
        "name": f"{base} cellular AHSS E1",
        "kind": "aanss",
        "text": "\n".join(rows) + "\n",
        "products": ahss_products,
        "construction": "C(alpha_1) = S^0 union_{alpha_1} e^4",
    }

    basis_names, degrees = table_basis(table_text)
    groups = {}
    for name in basis_names:
        groups.setdefault(degrees[name], []).append(name)
    h0_map = parse_product_table(h0)
    kernels, cokernels, e2_nodes = {}, {}, []

    for degree, domain in groups.items():
        if not all(name in h0_map for name in domain):
            continue
        target_degree = (degree[0] + 3, degree[1] + 1)
        target = groups.get(target_degree, [])
        if any(name not in target for source_name in domain for name in h0_map[source_name]):
            continue
        matrix = [[h0_map[source_name].get(target_name, 0) for target_name in target] for source_name in domain]
        transpose = [[matrix[i][j] for i in range(len(domain))] for j in range(len(target))]
        kernel_basis = nullspace(transpose, len(domain))
        kernels[degree] = (domain, kernel_basis)
        for vector in kernel_basis:
            terms = [(name, coefficient) for name, coefficient in zip(domain, vector) if coefficient]
            label = terms[0][0] if len(terms) == 1 and terms[0][1] == 1 else "(" + "+".join(("" if c == 1 else "2") + n for n, c in terms) + ")"
            e2_nodes.append({"name": f"top·{label}", "degree": (degree[0] + 4, degree[1]), "layer": "top", "vector": dict(terms), "sphere_degree": degree})

    for degree, target in groups.items():
        source_degree = (degree[0] - 3, degree[1] - 1)
        domain = groups.get(source_degree, [])
        if domain and not all(name in h0_map for name in domain):
            continue
        if any(name not in target for source_name in domain for name in h0_map.get(source_name, {})):
            continue
        matrix = [[h0_map[source_name].get(target_name, 0) for target_name in target] for source_name in domain]
        reduced, pivots = rref(matrix)
        free = [j for j in range(len(target)) if j not in pivots]
        cokernels[degree] = (target, reduced, pivots, free)
        for j in free:
            e2_nodes.append({"name": f"bottom·{target[j]}", "degree": degree, "layer": "bottom", "vector": {target[j]: 1}, "sphere_degree": degree})

    def apply_product(vector: dict[str, int], product_map: dict[str, dict[str, int]]) -> dict[str, int] | None:
        result = {}
        for name, coefficient in vector.items():
            if name not in product_map:
                return None
            for target, target_coefficient in product_map[name].items():
                result[target] = (result.get(target, 0) + coefficient * target_coefficient) % 3
        return {name: coefficient for name, coefficient in result.items() if coefficient}

    def induced_products() -> dict[str, str]:
        result = {}
        nodes_by_layer_degree = {}
        for node in e2_nodes:
            nodes_by_layer_degree.setdefault((node["layer"], node["sphere_degree"]), []).append(node)
        for label, text in products.items():
            product_map, output_rows = parse_product_table(text), []
            for node in e2_nodes:
                image = apply_product(node["vector"], product_map)
                if image is None or not image:
                    continue
                image_names = list(image)
                if any(name not in degrees for name in image_names):
                    continue
                target_degree = degrees[image_names[0]]
                if any(degrees[name] != target_degree for name in image_names):
                    continue
                candidates = nodes_by_layer_degree.get((node["layer"], target_degree), [])
                original_basis = groups.get(target_degree, [])
                vector = [image.get(name, 0) for name in original_basis]
                if node["layer"] == "bottom":
                    quotient = cokernels.get(target_degree)
                    if not quotient:
                        continue
                    _, reduced, pivots, _ = quotient
                    for row, pivot in enumerate(pivots):
                        factor = vector[pivot]
                        if factor:
                            vector = [(x - factor * y) % 3 for x, y in zip(vector, reduced[row])]
                candidate_vectors = [[candidate["vector"].get(name, 0) for name in original_basis] for candidate in candidates]
                coefficients = solve_in_basis(vector, candidate_vectors)
                if coefficients is None or not any(coefficients):
                    continue
                rhs = []
                for candidate, coefficient in zip(candidates, coefficients):
                    rhs.extend([candidate["name"]] * coefficient)
                output_rows.append(f"{node['name']}\t->\t" + "+".join(rhs) + "+o")
            result[label] = "\n".join(output_rows) + ("\n" if output_rows else "")
        return result

    e2_rows = [f"{node['name']}\t|deg=({node['degree'][0]},{node['degree'][1]})\t|cell={node['layer']}" for node in e2_nodes]
    e2 = {
        "name": f"{base} AANSS E2 after the cellular attaching differential",
        "kind": "aanss",
        "text": "\n".join(e2_rows) + "\n",
        "products": induced_products(),
        "construction": "H(E1(C(alpha_1)), d1=alpha_1=h0), over F3",
        "truncation_note": "Only bidegrees where every required h0 value is present are included.",
    }
    return ahss, e2


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
    parser.add_argument(
        "--no-products",
        action="store_true",
        help="omit companion multiplication tables from the generated payload",
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
            "products": {} if args.no_products else companion_products(source),
        }
        output = args.output_dir / f"{source.stem}.js"
        output.write_text(
            "globalThis.MINIMALRES_DATA = "
            + json.dumps(payload, ensure_ascii=False, indent=2)
            + ";\n",
            encoding="utf-8",
        )
        print(f"generated {output}")
        calpha1 = calpha1_payloads(source, payload["text"], payload["products"])
        if calpha1:
            ahss, e2 = calpha1
            base = source.stem.replace("AANSS_table", "CAlpha1")
            for suffix, data in (("AHSS", ahss), ("AANSS_E2", e2)):
                calpha1_output = args.output_dir / f"{base}_{suffix}.js"
                calpha1_output.write_text(
                    "globalThis.MINIMALRES_DATA = "
                    + json.dumps(data, ensure_ascii=False, indent=2)
                    + ";\n",
                    encoding="utf-8",
                )
                print(f"generated {calpha1_output}")


if __name__ == "__main__":
    main()
