#!/usr/bin/env python3
"""Tests for the cellular-AHSS-first C(alpha_1) chart conversion."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from generate_web_data import (  # noqa: E402
    calpha1_payloads,
    initial_h0_from_bockstein,
    initial_page_data,
    parse_product_table,
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
