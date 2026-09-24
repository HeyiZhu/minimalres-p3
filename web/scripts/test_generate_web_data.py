#!/usr/bin/env python3
"""Tests for the cellular-AHSS-first C(alpha_1) chart conversion."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from generate_web_data import (  # noqa: E402
    calpha1_payloads,
    companion_products,
    initial_h0_from_bockstein,
    initial_a0_from_names,
    initial_page_data,
    operation_family,
    pagewise_products,
    parse_product_table,
    product_spec,
    restrict_product_table,
)


SPHERE = """\
x	|deg=(0,0)
a	|deg=(3,1)
v	<-	u	|d2	|deg=(4,2)
"""

INITIAL_H0 = """\
x	->	a+o
a	->	o
u	->	o
v	->	o
"""


class InitialPageTest(unittest.TestCase):
    def test_product_families_and_defaults(self) -> None:
        self.assertEqual(operation_family("a0 (multiplication by 3)"), "a0")
        self.assertEqual(operation_family("h0 (alpha1)"), "alpha1")
        self.assertEqual(operation_family("theta3"), "theta3")
        self.assertTrue(product_spec("theta2", {"2": ""})["defaultVisible"])
        self.assertFalse(product_spec("h1", {"2": ""})["defaultVisible"])

    def test_product_rows_outside_displayed_basis_are_not_relabelled_zero(self) -> None:
        text = "x -> y+o\ny -> missing+o\nmissing -> o\n"
        restricted = restrict_product_table(text, {"x", "y"})
        self.assertEqual(restricted, "x -> y+o\n")

    def test_initial_a0_records_visible_v0_towers_only(self) -> None:
        table = """\
[0-0]\t|deg=(0,0)
v0^1[0-0]\t|deg=(0,1)
v0^2[0-0]\t|deg=(0,2)
x\t|deg=(4,1)
y\t|deg=(4,2)
"""
        a0, counts = initial_a0_from_names(
            table,
            internal_degree_bound=10,
        )
        operation = parse_product_table(a0)
        self.assertEqual(operation["[0-0]"], {"v0^1[0-0]": 1})
        self.assertEqual(operation["v0^1[0-0]"], {"v0^2[0-0]": 1})
        self.assertEqual(counts["unknown_rows"], 1)

    def test_pagewise_aanss_products_separate_e2_and_infinity(self) -> None:
        table = """\
[0-0]\t|deg=(0,0)
v0^1[0-0]\t|deg=(0,1)
"""
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "10_BPAANSS_table.txt"
            source.write_text(table, encoding="utf-8")
            products, counts = pagewise_products(
                source,
                table,
                {"a0 (multiplication by 3)": "[0-0]\t->\tv0^1[0-0]+o\n"},
            )
        spec = products["a0 (multiplication by 3)"]
        self.assertEqual(set(spec["pages"]), {"2", "infinity"})
        self.assertEqual(spec["family"], "a0")
        self.assertIn("[0-0]", spec["pages"]["2"])
        self.assertEqual(counts["a0 (multiplication by 3)"]["unknown_rows"], 0)

    def test_new_named_multiplier_is_discovered_and_gets_an_e2_page(self) -> None:
        table = "x\t|deg=(0,0)\ny\t|deg=(5,2)\n"
        relation = "x\t->\ty+o\ny\t->\to\n"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "10_BPAANSS_table.txt"
            source.write_text(table, encoding="utf-8")
            (root / "10_BPAANSS_custom.txt").write_text(
                relation,
                encoding="utf-8",
            )
            (root / "10_BPBocSS_custom.txt").write_text(
                relation,
                encoding="utf-8",
            )
            raw = companion_products(source)
            products, _ = pagewise_products(source, table, raw)
        self.assertIn("custom", products)
        self.assertEqual(set(products["custom"]["pages"]), {"2", "infinity"})
        self.assertEqual(products["custom"]["family"], "custom")
        self.assertFalse(products["custom"]["defaultVisible"])

    def test_differential_endpoints_are_initial_page_classes(self) -> None:
        names, degrees, differentials = initial_page_data(SPHERE)
        self.assertEqual(set(names), {"x", "a", "u", "v"})
        self.assertEqual(degrees["u"], (5, 0))
        self.assertEqual(differentials[0]["page"], 2)

    def test_cellular_homology_precedes_aanss_differentials(self) -> None:
        result = calpha1_payloads(
            Path("10_BPAANSS_table.txt"),
            SPHERE,
            {},
            initial_h0_text=INITIAL_H0,
        )
        self.assertIsNotNone(result)
        ahss, aanss = result
        self.assertIn("top·x\t->\tbottom·a", ahss["products"]["AHSS d1 = alpha1 = h0"])
        self.assertNotIn("bottom·a\t|deg=", aanss["text"])
        self.assertNotIn("top·x\t|deg=", aanss["text"])
        self.assertEqual(aanss["text"].count("|d2"), 2)
        self.assertIn("AANSS filtration", aanss["axis_note"])
        self.assertNotIn("Z/9", aanss["text"])

    def test_bockstein_h0_is_extended_by_differential_naturality(self) -> None:
        sphere = """\
v	<-	u	|d2	|deg=(4,2)
z	<-	w	|d2	|deg=(7,3)
"""
        h0, counts = initial_h0_from_bockstein(
            sphere,
            "",
            "u\t->\tw+o\nw\t->\to\n",
            internal_degree_bound=20,
        )
        operation = parse_product_table(h0)
        self.assertEqual(operation["u"], {"w": 1})
        self.assertEqual(operation["v"], {"z": 1})
        self.assertEqual(counts["unknown_h0_rows"], 0)


if __name__ == "__main__":
    unittest.main()
