#!/usr/bin/env python3
"""Generate the cell-filtered ANSS E2 data for C(alpha_1) at the prime 3.

Eva Belmont's algebraic-Novikov table gives the associated-graded pieces of
the sphere ANSS E2 page.  The companion a0 table assembles those pieces into
3-primary abelian groups, while the h0 table records multiplication by
alpha_1.  For each bidegree the cofiber long exact sequence gives canonical
cell-filtration pieces

    bottom: coker(h0),       top: ker(h0), shifted by the 4-cell.

The extension between those two pieces is not determined by these tables.
Consequently this script deliberately emits a cell-filtration associated
graded, with separate bottom and top roles, rather than claiming a direct-sum
decomposition of E2_ANSS(C alpha_1).

The operation tables use leading-term names as opaque identifiers.  Repeated
targets are coefficients modulo 3.  Eva's postprocessor discards the literal
``o`` tail, but the C++ writer uses it for the residual term at the current
filtered precision; it can therefore conceal terms beyond the table cutoff.
This generator follows Eva's table-level convention while recording that
finite-precision limitation explicitly.  A missing row means unknown, never
zero.
"""

from __future__ import annotations

import argparse
import itertools
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Sequence


PAYLOAD_PREFIX = "globalThis.MINIMALRES_DATA = "
DEGREE_RE = re.compile(r"\|deg=\((-?\d+),(-?\d+)\)")
FILTRATION_RE = re.compile(r"\[(-?\d+)-")
RUN_BOUND_RE = re.compile(r"^(\d+)_")
DEFAULT_SOURCE_URL = (
    "https://github.com/ebelmont/ANSS_data/tree/"
    "f5308980bc920d76a21b639b55b61f9e56b3d638/data"
)


Vector = tuple[int, ...]
Operation = dict[str, dict[str, int]]


@dataclass(frozen=True)
class Permanent:
    name: str
    stem: int
    filtration: int
    total_filtration: int

    @property
    def internal_degree(self) -> int:
        return self.stem + self.filtration


@dataclass(frozen=True)
class RoleClass:
    identifier: str
    stem: int
    filtration: int
    cell: str
    piece: str
    exponent: int | None
    representative: str
    sphere_stem: int
    sphere_filtration: int

    @property
    def order_label(self) -> str:
        return "Z_(3)" if self.exponent is None else f"Z/{3 ** self.exponent}"

    def table_line(self) -> str:
        details = (
            f"\t|cell={self.cell}"
            f"\t|piece={self.piece}"
            f"\t|group={self.order_label}"
            f"\t|representative={self.representative}"
            f"\t|sphere=({self.sphere_stem},{self.sphere_filtration})"
            "\t|cell-extension=unresolved"
            "\t|filtered-tail=discarded"
        )
        return (
            f"{self.identifier}\t|deg=({self.stem},{self.filtration})"
            f"{details}"
        )


def filtration(name: str, *, context: str) -> int:
    match = FILTRATION_RE.search(name)
    if match is None:
        raise ValueError(f"{context}: cannot read ANSS filtration from {name!r}")
    return int(match.group(1))


def parse_permanents(text: str) -> dict[str, Permanent]:
    """Read singleton algebraic-Novikov E-infinity names."""
    result: dict[str, Permanent] = {}
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        raw = raw_line.strip()
        if not raw or "<-" in raw:
            continue
        degree = DEGREE_RE.search(raw)
        if degree is None:
            raise ValueError(f"table line {line_number}: missing |deg=(stem,q)")
        name = raw.split("|", 1)[0].strip()
        if name in result:
            raise ValueError(f"table line {line_number}: duplicate permanent {name!r}")
        stem, total_filtration = map(int, degree.groups())
        result[name] = Permanent(
            name=name,
            stem=stem,
            filtration=filtration(name, context=f"table line {line_number}"),
            total_filtration=total_filtration,
        )
    if not result:
        raise ValueError("sphere table has no singleton/permanent records")
    return result


def parse_operation(text: str, *, table_name: str) -> Operation:
    result: Operation = {}
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        raw = raw_line.strip()
        if not raw:
            continue
        parts = re.split(r"\s*->\s*", raw, maxsplit=1)
        if len(parts) != 2:
            raise ValueError(f"{table_name} line {line_number}: missing ->")
        source, rhs = parts
        if source in result:
            raise ValueError(
                f"{table_name} line {line_number}: duplicate source {source!r}"
            )
        multiplicities: Counter[str] = Counter(
            term.strip()
            for term in rhs.split("+")
            if term.strip() and term.strip() != "o"
        )
        result[source] = {
            target: multiplicity % 3
            for target, multiplicity in multiplicities.items()
            if multiplicity % 3
        }
    return result


def parse_payload(path: Path) -> dict[str, object]:
    raw = path.read_text(encoding="utf-8").strip()
    if not raw.startswith(PAYLOAD_PREFIX) or not raw.endswith(";"):
        raise ValueError(f"{path}: not a MinimalResolution JavaScript payload")
    return json.loads(raw[len(PAYLOAD_PREFIX) : -1])


def select_product(products: object, prefix: str) -> str:
    if not isinstance(products, dict):
        raise ValueError("sphere payload has no product dictionary")
    matches = [value for label, value in products.items() if str(label).startswith(prefix)]
    if len(matches) != 1 or not isinstance(matches[0], str):
        raise ValueError(f"expected exactly one {prefix!r} product table in payload")
    return matches[0]


def read_input(source: Path) -> tuple[str, str, str, str, int | None]:
    """Return sphere, a0, h0, run label, and declared internal-degree bound."""
    if source.suffix.lower() == ".js":
        payload = parse_payload(source)
        sphere = payload.get("text")
        if not isinstance(sphere, str):
            raise ValueError(f"{source}: payload has no text table")
        products = payload.get("products")
        name = str(payload.get("name", source.stem))
        run_match = RUN_BOUND_RE.match(name)
        return (
            sphere,
            select_product(products, "a0"),
            select_product(products, "h0"),
            name.split("_", 1)[0],
            int(run_match.group(1)) if run_match else None,
        )

    if not source.name.endswith("BPAANSS_table.txt"):
        raise ValueError(
            "text input must be named like N_BPAANSS_table.txt so companion "
            "a0 and h0 files can be found"
        )
    prefix = source.name[: -len("BPAANSS_table.txt")]
    a0_path = source.with_name(prefix + "BPAANSS_a0.txt")
    h0_path = source.with_name(prefix + "BPAANSS_h0.txt")
    for companion in (a0_path, h0_path):
        if not companion.is_file():
            raise ValueError(f"missing companion table: {companion}")
    run_match = RUN_BOUND_RE.match(source.name)
    return (
        source.read_text(encoding="utf-8"),
        a0_path.read_text(encoding="utf-8"),
        h0_path.read_text(encoding="utf-8"),
        prefix.rstrip("_"),
        int(run_match.group(1)) if run_match else None,
    )


class PGroup:
    """A finite 3-group with triangular relations 3 e_i = relation_i."""

    def __init__(
        self,
        nodes: Sequence[Permanent],
        a0: Operation,
        permanents: dict[str, Permanent],
    ) -> None:
        self.nodes = tuple(sorted(nodes, key=lambda node: (node.total_filtration, node.name)))
        self.names = tuple(node.name for node in self.nodes)
        self.index = {name: i for i, name in enumerate(self.names)}
        self.dimension = len(self.names)
        self.zero: Vector = (0,) * self.dimension
        relations: list[Vector] = []

        for node in self.nodes:
            if node.name not in a0:
                raise ValueError(
                    f"missing a0 row for {node.name!r} at "
                    f"({node.stem},{node.filtration})"
                )
            relation = [0] * self.dimension
            for target, coefficient in a0[node.name].items():
                target_node = permanents.get(target)
                if target_node is None:
                    raise ValueError(f"a0 target {target!r} is not permanent")
                if (target_node.stem, target_node.filtration) != (
                    node.stem,
                    node.filtration,
                ):
                    raise ValueError(f"a0 has wrong bidegree: {node.name!r} -> {target!r}")
                if target not in self.index:
                    raise ValueError(f"a0 target {target!r} is outside its sphere group")
                if target_node.total_filtration <= node.total_filtration:
                    raise ValueError(
                        f"a0 relation is not triangular: {node.name!r} -> {target!r}"
                    )
                relation[self.index[target]] = coefficient
            relations.append(tuple(relation))

        self.relations = tuple(relations)
        self.elements: tuple[Vector, ...] = tuple(
            itertools.product(range(3), repeat=self.dimension)
        )

    def reduce(self, vector: Iterable[int]) -> Vector:
        values = list(vector)
        if len(values) != self.dimension:
            raise ValueError("vector has the wrong dimension")
        for i in range(self.dimension):
            quotient, values[i] = divmod(values[i], 3)
            if quotient:
                for j, coefficient in enumerate(self.relations[i]):
                    values[j] += quotient * coefficient
        return tuple(values)

    def add(self, left: Vector, right: Vector) -> Vector:
        return self.reduce(a + b for a, b in zip(left, right))

    def mul(self, scalar: int, vector: Vector) -> Vector:
        return self.reduce(scalar * value for value in vector)

    def basis(self, index: int) -> Vector:
        values = [0] * self.dimension
        values[index] = 1
        return tuple(values)

    def format(self, vector: Vector) -> str:
        terms: list[str] = []
        for coefficient, name in zip(vector, self.names):
            if coefficient == 1:
                terms.append(name)
            elif coefficient == 2:
                terms.append(f"2*{name}")
        return "+".join(terms) if terms else "0"


class FiniteRoleGroup:
    """A finite subgroup or quotient, with operations inherited from a PGroup."""

    def __init__(
        self,
        elements: Iterable[Vector],
        zero: Vector,
        add: Callable[[Vector, Vector], Vector],
        mul: Callable[[int, Vector], Vector],
        format_rep: Callable[[Vector], str],
    ) -> None:
        self.elements = tuple(sorted(set(elements)))
        self.zero = zero
        self.add = add
        self.mul = mul
        self.format = format_rep
        if zero not in self.elements:
            raise ValueError("finite role group does not contain zero")


def map_element(
    source: PGroup,
    target: PGroup,
    h0: Operation,
    vector: Vector,
) -> Vector:
    output = [0] * target.dimension
    for i, digit in enumerate(vector):
        if not digit:
            continue
        source_name = source.names[i]
        if source_name not in h0:
            raise ValueError(f"missing h0 row for {source_name!r}")
        for target_name, coefficient in h0[source_name].items():
            if target_name not in target.index:
                raise ValueError(
                    f"h0 target {target_name!r} is not in the expected target group"
                )
            output[target.index[target_name]] += digit * coefficient
    return target.reduce(output)


def validate_h0_map(source: PGroup, target: PGroup, h0: Operation) -> None:
    for node in source.nodes:
        if node.name not in h0:
            raise ValueError(f"missing h0 row for {node.name!r}")
        for target_name in h0[node.name]:
            target_node = next(
                (candidate for candidate in target.nodes if candidate.name == target_name),
                None,
            )
            if target_node is None:
                raise ValueError(f"h0 target {target_name!r} is not permanent in range")
            if (
                target_node.stem - node.stem,
                target_node.filtration - node.filtration,
            ) != (3, 1):
                raise ValueError(f"h0 has wrong bidegree: {node.name!r} -> {target_name!r}")

    for i in range(source.dimension):
        basis = source.basis(i)
        left = map_element(source, target, h0, source.mul(3, basis))
        right = target.mul(3, map_element(source, target, h0, basis))
        if left != right:
            raise ValueError(f"h0 does not respect the a0 relation on {source.names[i]!r}")


def kernel_group(source: PGroup, target: PGroup, h0: Operation) -> FiniteRoleGroup:
    validate_h0_map(source, target, h0)
    elements = [
        element
        for element in source.elements
        if map_element(source, target, h0, element) == target.zero
    ]
    return FiniteRoleGroup(elements, source.zero, source.add, source.mul, source.format)


def image_of_map(source: PGroup, target: PGroup, h0: Operation) -> set[Vector]:
    validate_h0_map(source, target, h0)
    return {map_element(source, target, h0, element) for element in source.elements}


def quotient_group(target: PGroup, image: set[Vector]) -> FiniteRoleGroup:
    if target.zero not in image:
        raise ValueError("image is not a subgroup")
    canonical: dict[Vector, Vector] = {}
    for element in target.elements:
        coset = {target.add(element, member) for member in image}
        representative = min(coset)
        for member in coset:
            canonical[member] = representative
    quotient_elements = set(canonical.values())

    def add(left: Vector, right: Vector) -> Vector:
        return canonical[target.add(left, right)]

    def mul(scalar: int, vector: Vector) -> Vector:
        return canonical[target.mul(scalar, vector)]

    return FiniteRoleGroup(
        quotient_elements,
        canonical[target.zero],
        add,
        mul,
        target.format,
    )


def exact_log3(value: int) -> int:
    exponent = 0
    while value > 1 and value % 3 == 0:
        value //= 3
        exponent += 1
    if value != 1:
        raise ValueError("group cardinality is not a power of 3")
    return exponent


def invariant_exponents(group: FiniteRoleGroup) -> list[int]:
    """Return e for each cyclic factor Z/3^e, largest first."""
    log_order = exact_log3(len(group.elements))
    if log_order == 0:
        return []
    killed_logs = [0]
    for exponent in range(1, log_order + 1):
        killed = sum(
            1
            for element in group.elements
            if group.mul(3**exponent, element) == group.zero
        )
        killed_logs.append(exact_log3(killed))
        if killed == len(group.elements):
            break
    at_least = [
        killed_logs[index] - killed_logs[index - 1]
        for index in range(1, len(killed_logs))
    ]
    result: list[int] = []
    for exponent, count in enumerate(at_least, start=1):
        next_count = at_least[exponent] if exponent < len(at_least) else 0
        result.extend([exponent] * (count - next_count))
    return sorted(result, reverse=True)


def element_exponent(group: FiniteRoleGroup, element: Vector) -> int:
    if element == group.zero:
        return 0
    bound = exact_log3(len(group.elements))
    value = element
    for exponent in range(1, bound + 1):
        value = group.mul(3, value)
        if value == group.zero:
            return exponent
    raise ValueError("element order exceeds group order")


def decomposition_generators(
    group: FiniteRoleGroup, exponents: Sequence[int]
) -> list[Vector]:
    all_elements = set(group.elements)
    candidates: dict[int, list[tuple[Vector, set[Vector]]]] = {}
    for exponent in set(exponents):
        candidates[exponent] = []
        for candidate in group.elements:
            if element_exponent(group, candidate) == exponent:
                cyclic = {
                    group.mul(scalar, candidate) for scalar in range(3**exponent)
                }
                candidates[exponent].append((candidate, cyclic))

    def search(
        position: int,
        generated: set[Vector],
        chosen: list[Vector],
    ) -> tuple[list[Vector], set[Vector]] | None:
        if position == len(exponents):
            return (chosen, generated) if generated == all_elements else None
        exponent = exponents[position]
        for candidate, cyclic in candidates[exponent]:
            closure = {
                group.add(existing, multiple)
                for existing in generated
                for multiple in cyclic
            }
            if len(closure) != len(generated) * (3**exponent):
                continue
            result = search(position + 1, closure, [*chosen, candidate])
            if result is not None:
                return result
        return None

    result = search(0, {group.zero}, [])
    if result is None:
        raise ValueError("could not choose cyclic direct-factor generators")
    chosen, generated = result
    if generated != all_elements:
        raise ValueError("chosen cyclic factors do not generate the role group")
    return chosen


def group_nodes(
    permanents: dict[str, Permanent]
) -> dict[tuple[int, int], list[Permanent]]:
    result: dict[tuple[int, int], list[Permanent]] = defaultdict(list)
    for node in permanents.values():
        result[(node.stem, node.filtration)].append(node)
    return dict(result)


def build_groups(
    permanents: dict[str, Permanent],
    a0: Operation,
) -> tuple[dict[tuple[int, int], PGroup], set[tuple[int, int]]]:
    groups: dict[tuple[int, int], PGroup] = {}
    incomplete: set[tuple[int, int]] = set()
    for bidegree, nodes in group_nodes(permanents).items():
        if bidegree == (0, 0):
            continue
        if any(node.name not in a0 for node in nodes):
            incomplete.add(bidegree)
            continue
        groups[bidegree] = PGroup(nodes, a0, permanents)
    return groups, incomplete


def infer_safe_max_stem(
    permanents: dict[str, Permanent],
    h0: Operation,
    incomplete_a0: set[tuple[int, int]],
    internal_degree_bound: int,
) -> int:
    unsafe_h0_stems: list[int] = []
    for bidegree, nodes in group_nodes(permanents).items():
        if bidegree == (0, 0):
            continue
        if any(
            node.name not in h0 or node.internal_degree > internal_degree_bound - 4
            for node in nodes
        ):
            unsafe_h0_stems.append(bidegree[0])
    candidates = [stem + 2 for stem in unsafe_h0_stems]
    candidates.extend(stem - 1 for stem, _ in incomplete_a0)
    if not candidates:
        raise ValueError("cannot infer a finite safe chart range")
    return min(candidates)


def trivial_group() -> PGroup:
    return PGroup((), {}, {})


def make_role_records(
    sphere_text: str,
    a0_text: str,
    h0_text: str,
    *,
    max_stem: int | None,
    internal_degree_bound: int,
) -> tuple[list[RoleClass], dict[str, object]]:
    permanents = parse_permanents(sphere_text)
    a0 = parse_operation(a0_text, table_name="a0")
    h0 = parse_operation(h0_text, table_name="h0")
    groups, incomplete_a0 = build_groups(permanents, a0)
    inferred_max = infer_safe_max_stem(
        permanents, h0, incomplete_a0, internal_degree_bound
    )
    if max_stem is None:
        max_stem = inferred_max
    if max_stem > inferred_max:
        raise ValueError(
            f"requested stem {max_stem} exceeds the row-complete table range "
            f"through stem {inferred_max}"
        )

    zero_group = trivial_group()
    records: list[RoleClass] = []
    order_histogram: Counter[str] = Counter()
    finite_bottom = 0
    finite_top = 0

    def append_factors(
        role_group: FiniteRoleGroup,
        *,
        cell: str,
        display_bidegree: tuple[int, int],
        sphere_bidegree: tuple[int, int],
    ) -> None:
        nonlocal finite_bottom, finite_top
        exponents = invariant_exponents(role_group)
        representatives = decomposition_generators(role_group, exponents)
        prefix = "b" if cell == "bottom" else "t"
        piece = "coker(h0)" if cell == "bottom" else "ker(h0)"
        for index, (exponent, representative) in enumerate(
            zip(exponents, representatives), start=1
        ):
            stem, filt = display_bidegree
            records.append(
                RoleClass(
                    identifier=f"calpha1_{prefix}_{stem}_{filt}_{index}",
                    stem=stem,
                    filtration=filt,
                    cell=cell,
                    piece=piece,
                    exponent=exponent,
                    representative=role_group.format(representative),
                    sphere_stem=sphere_bidegree[0],
                    sphere_filtration=sphere_bidegree[1],
                )
            )
            order_histogram[str(3**exponent)] += 1
            if cell == "bottom":
                finite_bottom += 1
            else:
                finite_top += 1

    # The unit tower is the unique truncated free Z_(3) summand.  Multiplication
    # by h0 maps its unit onto alpha_1, so its kernel is 3 Z_(3) ~= Z_(3).
    alpha = groups.get((3, 1))
    if alpha is None or len(alpha.elements) != 3:
        raise ValueError("expected alpha_1 to generate a Z/3 sphere group")
    unit_h0 = h0.get("[0-0]")
    if unit_h0 is None or set(unit_h0) != set(alpha.names):
        raise ValueError("unit h0 row does not map onto the alpha_1 group")
    free_records = [
            RoleClass(
                "calpha1_b_0_0_1",
                0,
                0,
                "bottom",
                "coker(h0)",
                None,
                "[0-0]",
                0,
                0,
            ),
            RoleClass(
                "calpha1_t_4_0_1",
                4,
                0,
                "top",
                "ker(h0)",
                None,
                "3*[0-0]",
                0,
                0,
            ),
        ]
    free_records = [record for record in free_records if record.stem <= max_stem]
    records.extend(free_records)
    free_bottom = sum(record.cell == "bottom" for record in free_records)
    free_top = sum(record.cell == "top" for record in free_records)
    order_histogram["3-local"] = len(free_records)

    # Bottom-cell cokernel pieces.
    for target_bidegree in sorted(groups):
        target_stem, target_filtration = target_bidegree
        if target_stem > max_stem:
            continue
        target = groups[target_bidegree]
        source_bidegree = (target_stem - 3, target_filtration - 1)
        if source_bidegree == (0, 0):
            # The unit maps onto all of the alpha_1 group.
            image = set(target.elements)
        else:
            if source_bidegree in incomplete_a0:
                raise ValueError(f"incomplete incoming sphere group {source_bidegree}")
            source = groups.get(source_bidegree)
            if source is None:
                image = {target.zero}
            else:
                for node in source.nodes:
                    if (
                        node.name not in h0
                        or node.internal_degree > internal_degree_bound - 4
                    ):
                        raise ValueError(
                            f"unsafe h0 source {node.name!r} affects bottom stem "
                            f"{target_stem}"
                        )
                image = image_of_map(source, target, h0)
        append_factors(
            quotient_group(target, image),
            cell="bottom",
            display_bidegree=target_bidegree,
            sphere_bidegree=target_bidegree,
        )

    # Top-cell kernel pieces, shifted right by the 4-cell.
    for source_bidegree in sorted(groups):
        source_stem, source_filtration = source_bidegree
        display_bidegree = (source_stem + 4, source_filtration)
        if display_bidegree[0] > max_stem:
            continue
        source = groups[source_bidegree]
        for node in source.nodes:
            if node.name not in h0 or node.internal_degree > internal_degree_bound - 4:
                raise ValueError(
                    f"unsafe h0 source {node.name!r} affects top stem "
                    f"{display_bidegree[0]}"
                )
        target_bidegree = (source_stem + 3, source_filtration + 1)
        target = groups.get(target_bidegree, zero_group)
        if target is zero_group:
            if any(h0[node.name] for node in source.nodes):
                raise ValueError(f"nonzero h0 map has no target group {target_bidegree}")
        append_factors(
            kernel_group(source, target, h0),
            cell="top",
            display_bidegree=display_bidegree,
            sphere_bidegree=source_bidegree,
        )

    records.sort(key=lambda item: (item.stem, item.filtration, item.cell, item.identifier))
    roles_by_bidegree: dict[tuple[int, int], set[str]] = defaultdict(set)
    for record in records:
        roles_by_bidegree[(record.stem, record.filtration)].add(record.cell)
    counts: dict[str, object] = {
        "bottom": finite_bottom + free_bottom,
        "top": finite_top + free_top,
        "finite_bottom": finite_bottom,
        "finite_top": finite_top,
        "free": len(free_records),
        "classes": len(records),
        "orders": dict(sorted(order_histogram.items())),
        "row_safe_max_stem": max_stem,
        "inferred_row_safe_max_stem": inferred_max,
        "bidegrees_with_both_roles": sum(
            roles == {"bottom", "top"} for roles in roles_by_bidegree.values()
        ),
        "sphere_permanent_pieces": len(permanents),
        "a0_rows": len(a0),
        "h0_rows": len(h0),
        "algebraic_novikov_filtration_cutoff": (
            max(node.total_filtration for node in permanents.values()) + 1
        ),
    }
    return records, counts


def output_name(run_label: str) -> str:
    return f"{run_label}_Calpha1_ANSS_E2.js"


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Generate the kernel/cokernel cell filtration of "
            "E2_ANSS(C alpha_1) from sphere AANSS, a0, and h0 data."
        )
    )
    parser.add_argument(
        "source",
        type=Path,
        help="N_BPAANSS_table.txt or an existing N_BPAANSS_table.js payload",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "data",
    )
    parser.add_argument("--max-stem", type=int)
    parser.add_argument(
        "--internal-degree-bound",
        type=int,
        help="declared sphere run bound; inferred from the N_ filename by default",
    )
    parser.add_argument("--source-url", default=DEFAULT_SOURCE_URL)
    args = parser.parse_args()

    if not args.source.is_file():
        parser.error(f"source does not exist: {args.source}")
    try:
        sphere, a0, h0, run_label, inferred_bound = read_input(args.source)
        internal_bound = args.internal_degree_bound or inferred_bound
        if internal_bound is None:
            parser.error("cannot infer the internal-degree bound; pass --internal-degree-bound")
        records, counts = make_role_records(
            sphere,
            a0,
            h0,
            max_stem=args.max_stem,
            internal_degree_bound=internal_bound,
        )
    except ValueError as error:
        parser.error(str(error))

    filtration_cutoff = counts["algebraic_novikov_filtration_cutoff"]
    payload = {
        "name": (
            f"{run_label} C alpha1 ANSS E2 — truncated kernel/cokernel model"
        ),
        "kind": "two-cell",
        "description": (
            "Cell-filtration associated graded of Eva's algebraic-Novikov-"
            f"filtration-<{filtration_cutoff} approximation to "
            "E2_ANSS(C alpha1). Displayed "
            "orders are invariant factors of the bottom-cokernel and shifted "
            "top-kernel subquotients, conditional on discarding unrecorded "
            "filtered o-tails. The additive extension between cell roles is "
            "also not determined by the tables."
        ),
        "source": args.source_url,
        "cell_extension_unresolved": True,
        "filtered_remainder_discarded": True,
        "range_certification": (
            "row-complete relative to the internal-degree and algebraic-"
            "Novikov filtration cutoffs; not a proof that filtration >= "
            f"{filtration_cutoff} tails vanish"
        ),
        "cellLabels": {
            "bottom": "image of bottom-cell inclusion: coker(h0)",
            "top": (
                "image under top-cell projection: shifted ker(h0); "
                "lift noncanonical"
            ),
        },
        "counts": counts,
        "text": "\n".join(record.table_line() for record in records) + "\n",
        "products": {},
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / output_name(run_label)
    output.write_text(
        PAYLOAD_PREFIX + json.dumps(payload, ensure_ascii=False, indent=2) + ";\n",
        encoding="utf-8",
    )
    print(
        f"generated {output}: {counts['classes']} cell-role records "
        f"({counts['bottom']} bottom, {counts['top']} top), row-safe through "
        f"stem {counts['row_safe_max_stem']}"
    )
    print(
        "finite orders: "
        + ", ".join(
            f"{count} x {('Z_(3)' if order == '3-local' else 'Z/' + order)}"
            for order, count in counts["orders"].items()
        )
    )


if __name__ == "__main__":
    main()
