#!/usr/bin/env python3
"""Regression tests for the M(3) web-data extraction rules."""

from __future__ import annotations

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_m3_web_data import extract_moore_classes, normalize_product_table


SAMPLE = """\
[0-0]\t|deg=0
[1-0]\t|deg=7
v0^1[1-0]\t<-\tv1^1[0-0]\t|d1\t|deg=7
v1^1[1-1]\t<-\tv2^1[0-0]\t|d0\t|deg=31
v0^2v1^2[1-0]\t<-\tv1^3[0-0]\t|d2\t|deg=23
"""


class MooreExtractionTest(unittest.TestCase):
    def test_one_copy_basis_and_grading(self) -> None:
        classes, counts = extract_moore_classes(SAMPLE)
        self.assertEqual([item.name for item in classes], [
            "[0-0]",
            "[1-0]",
            "v1^1[0-0]",
            "v1^3[0-0]",
        ])
        self.assertEqual(
            [(item.stem, item.filtration, item.cell) for item in classes],
            [(0, 0, "bottom"), (3, 1, "bottom"), (4, 0, "top"), (12, 0, "top")],
        )
        self.assertEqual(counts["classes"], 4)
        self.assertEqual(counts["bottom"], 2)
        self.assertEqual(counts["top"], 2)
        self.assertEqual(counts["d0_pairs"], 1)
        self.assertEqual(counts["d1_sources"], 1)
        self.assertEqual(counts["d2_sources"], 1)

    def test_rejects_inconsistent_filtrations(self) -> None:
        bad = "v0^1[2-0]\t<-\tv1^1[0-0]\t|d1\t|deg=8\n"
        with self.assertRaisesRegex(ValueError, "adjacent ANSS filtrations"):
            extract_moore_classes(bad)

    def test_product_normalization_reduces_coefficients_mod_three(self) -> None:
        classes, _ = extract_moore_classes(SAMPLE)
        basis = {item.name: item for item in classes}
        table = """\
[0-0] -> v1^1[0-0]+v1^1[0-0]
[1-0] -> o
v1^1[0-0] -> o
v1^3[0-0] -> o
not-a-basis-name -> also-not-a-basis-name
"""
        normalized, stats = normalize_product_table(
            table, basis, (4, 0), table_name="sample"
        )
        self.assertEqual(
            normalized,
            "[0-0]\t->\tv1^1[0-0]+v1^1[0-0]\n",
        )
        self.assertEqual(stats["source_rows"], 4)
        self.assertEqual(stats["nonzero_rows"], 1)
        self.assertEqual(stats["distinct_targets"], 1)
        self.assertEqual(stats["coefficient_two_targets"], 1)


if __name__ == "__main__":
    unittest.main()
