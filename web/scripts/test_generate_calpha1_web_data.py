#!/usr/bin/env python3
"""Regression tests for the C(alpha_1) ANSS E2 cell-filtration generator."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from generate_calpha1_web_data import (  # noqa: E402
    PGroup,
    Permanent,
    image_of_map,
    invariant_exponents,
    kernel_group,
    make_role_records,
    parse_operation,
    quotient_group,
    read_input,
)


REPOSITORY = Path(__file__).resolve().parents[2]
SPHERE_PAYLOAD = REPOSITORY / "web" / "data" / "185_BPAANSS_table.js"


class SmallPresentationTest(unittest.TestCase):
    def test_exact_kernel_and_cokernel_over_nontrivial_three_extension(self) -> None:
        x0 = Permanent("x0[1-0]", 7, 1, 1)
        x1 = Permanent("x1[1-1]", 7, 1, 2)
        y = Permanent("y[2-0]", 10, 2, 2)
        permanents = {node.name: node for node in (x0, x1, y)}
        a0 = {
            x0.name: {x1.name: 1},
            x1.name: {},
            y.name: {},
        }
        source = PGroup((x0, x1), a0, permanents)
        target = PGroup((y,), a0, permanents)
        h0 = {x0.name: {y.name: 1}, x1.name: {}}

        self.assertEqual(invariant_exponents(kernel_group(source, target, h0)), [1])
        image = image_of_map(source, target, h0)
        self.assertEqual(invariant_exponents(quotient_group(target, image)), [])

    def test_repeated_operation_terms_are_coefficients_mod_three(self) -> None:
        operation = parse_operation("x -> y+y+y+y+o\n", table_name="sample")
        self.assertEqual(operation, {"x": {"y": 1}})


class Eva185IntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        sphere, a0, h0, _, bound = read_input(SPHERE_PAYLOAD)
        if bound is None:
            raise AssertionError("the 185 payload did not expose its run bound")
        cls.inputs = (sphere, a0, h0, bound)
        cls.records, cls.counts = make_role_records(
            sphere,
            a0,
            h0,
            max_stem=None,
            internal_degree_bound=bound,
        )

    def test_certified_counts_and_orders(self) -> None:
        self.assertEqual(self.counts["row_safe_max_stem"], 153)
        self.assertEqual(self.counts["bidegrees_with_both_roles"], 86)
        self.assertEqual(self.counts["algebraic_novikov_filtration_cutoff"], 40)
        self.assertEqual(self.counts["classes"], 451)
        self.assertEqual(self.counts["bottom"], 236)
        self.assertEqual(self.counts["top"], 215)
        self.assertEqual(
            self.counts["orders"],
            {"3": 420, "3-local": 2, "9": 20, "27": 7, "81": 2},
        )
        self.assertEqual(len({record.identifier for record in self.records}), 451)

    def test_low_stem_long_exact_sequence_checks(self) -> None:
        def groups(stem: int, filtration: int, cell: str) -> list[str]:
            return sorted(
                record.order_label
                for record in self.records
                if (record.stem, record.filtration, record.cell)
                == (stem, filtration, cell)
            )

        self.assertEqual(groups(0, 0, "bottom"), ["Z_(3)"])
        self.assertEqual(groups(4, 0, "top"), ["Z_(3)"])
        self.assertEqual(groups(3, 1, "bottom"), [])
        self.assertEqual(groups(7, 1, "bottom"), ["Z/3"])
        self.assertEqual(groups(7, 1, "top"), ["Z/3"])
        self.assertEqual(groups(10, 2, "bottom"), ["Z/3"])
        self.assertEqual(groups(11, 1, "bottom"), ["Z/9"])
        self.assertEqual(groups(11, 1, "top"), ["Z/3"])

    def test_generator_refuses_the_first_uncertified_stem(self) -> None:
        sphere, a0, h0, bound = self.inputs
        with self.assertRaisesRegex(ValueError, "table range through stem 153"):
            make_role_records(
                sphere,
                a0,
                h0,
                max_stem=154,
                internal_degree_bound=bound,
            )

    def test_requested_stem_bound_applies_to_the_free_top_cell(self) -> None:
        sphere, a0, h0, bound = self.inputs
        records, counts = make_role_records(
            sphere,
            a0,
            h0,
            max_stem=3,
            internal_degree_bound=bound,
        )
        self.assertEqual([(record.stem, record.cell) for record in records], [(0, "bottom")])
        self.assertEqual(counts["free"], 1)


if __name__ == "__main__":
    unittest.main()
