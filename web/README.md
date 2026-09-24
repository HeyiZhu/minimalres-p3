# MinimalResolution chart reader

Serve this directory with any static web server, for example:

```sh
cd web
python3 -m http.server 4173
```

Then open `http://localhost:4173` in a browser. The small prime-3 AANSS
example is displayed initially. A generated dataset can be selected in the URL,
in the same style as SSeqCpp:

```text
http://localhost:4173/?data=10_BPAANSS_table
http://localhost:4173/?data=10_BPBocSS_table
http://localhost:4173/?data=185_BPAANSS_table
http://localhost:4173/?data=185_BPBocSS_table
http://localhost:4173/?data=185_M3_ANSS_E2
http://localhost:4173/?data=185_Calpha1_ANSS_E2
```

The value after `?data=` is the generated JavaScript filename without `.js`.
You can also use **Open table** to read a `.txt` file directly without first
generating JavaScript.

## Generate webpage data

From the repository root, convert one or more result tables with:

```sh
python3 web/scripts/generate_web_data.py \
  run-p3-d10-l2-fixed/10_BPAANSS_table.txt \
  run-p3-d10-l2-fixed/10_BPBocSS_table.txt
```

This writes `web/data/10_BPAANSS_table.js` and
`web/data/10_BPBocSS_table.js`. If a source table changes, run the same command
again and refresh the browser. No rebuild or package installation is needed.

The reader parses data entirely in the browser; selected local files are not
uploaded anywhere.

## Multiplication overlays

Use the **Products** drop-down at the upper right to turn individual
multiplications on or off. The default selection is multiplication by `a0`,
`alpha1 = h0`, and every available `theta` operation. Other tables such as
`h1` and `h2` remain available in the menu when their companion files exist,
but start unchecked. **Defaults** restores this selection and **None** hides
all product lines.

Newly generated AANSS datasets store product relations separately by page:

* page `2` records the initial AANSS relation where it can be established from
  the named initial basis and the earlier Bockstein operation;
* page `infinity` records the existing C++ chain-level multiplier expressed in
  the surviving AANSS basis.

When an intermediate finite page has no table of its own, the reader carries
the latest earlier finite-page relation forward and removes lines whose source
or target has died. It does not use an `E2` relation as an `E∞` relation: the
explicit `infinity` table is selected there. Rows that cannot be determined
within the calculation range are omitted rather than declared zero. The
generated payload includes `product_page_counts` so known and unknown initial
rows can be audited.

The browser format remains backward compatible with the earlier
`"label": "source -> target"` objects. Its page-aware form is:

```json
{
  "a0 (multiplication by 3)": {
    "family": "a0",
    "defaultVisible": true,
    "pages": {
      "2": "source -> E2-target+o\n",
      "infinity": "source -> surviving-target+o\n"
    },
    "provenance": {
      "2": "how the initial-page table was obtained",
      "infinity": "how the surviving table was obtained"
    }
  }
}
```

At the chain-complex level, `BPInit::mult_table(mul, degree, filename)` is the
generic entry point for a fixed `BP_*BP` multiplier. It constructs the
multiplier on the resolution and writes both `AANSS_<filename>` and
`BocSS_<filename>`. The web generator automatically discovers additional
matching `AANSS_<name>.txt`/`BocSS_<name>.txt` files. If their visible terms
have one unambiguous bidegree shift, it records the projected `E2` operation;
otherwise it retains the authoritative `E∞` table and reports no invented
initial-page relation. The current repository defines `h0 = alpha1` and the Moore
`theta2` through `theta7` multipliers. It does not yet define sphere `h1` or
`h2` elements in `BP_Op`; adding those requires a mathematically verified
`BP_*BP` representative and grading before calling the generic function.

Conceptually this is the fixed-class part of the Yoneda product: a chosen
cocycle is lifted to a filtered chain map of the resolution, and composition
induces its action on Ext. A complete multiplication table for arbitrary pairs
of Ext classes would require storing compatible lifts (or an equivalent
diagonal/cobar product), not merely multiplying the printed class names. Once
the filtered chain map is retained page by page, its commutation with the
differential supplies the Leibniz propagation used by the `E2` reconstruction.
The reusable converter function is
`extend_right_product_by_leibniz(known, differentials, label=...)`; it applies
`d_r(xm)=d_r(x)m` for a permanent right multiplier and rejects a table that
conflicts with an already known row.

## Eva Belmont's 185 computation

The four checked-in 185 datasets are derived from the public text files in
[ebelmont/ANSS_data](https://github.com/ebelmont/ANSS_data/tree/master/data):

* `185_BPAANSS_table.js` displays the algebraic Novikov spectral sequence for
  the sphere. Its `E∞` view is the associated graded of the Adams--Novikov
  `E2` page; it is not an automatic solution of the remaining 3-extensions.
  The small companion tables for multiplication by 3 (`a0`) and by
  alpha_1 (`h0`) are bundled.
* `185_BPBocSS_table.js` displays the raw Bockstein computation. It opens on
  Bockstein `E1`, after the extraneous `d0` pairs have died. Select `E0` to see
  those pairs. This compact payload deliberately omits the roughly 68 MB of
  companion operation tables.
* `185_M3_ANSS_E2.js` is the normalized, one-copy additive basis of
  `E2_ANSS(M3)`: 513 bottom-cell classes (black) and 512 top-cell classes
  (hollow purple). The on-chart legend records these as bottom-cell classes
  with zero boundary and top-cell classes with nonzero boundary; this does not
  assert a noncanonical splitting of the Moore long exact sequence. It
  discards 11,537 `d0` pairs and does not count a positive
  Bockstein target as another Moore class, since that target is a filtered
  3-adic copy of a bottom class already represented once. Its compact product
  menu contains the normalized `h0` (alpha_1) and `theta2` through `theta7`
  operations. Solid green product lines have coefficient 1; dashed green lines
  have coefficient 2 modulo 3.
* `185_Calpha1_ANSS_E2.js` is a truncated additive target model for
  `E2_ANSS(C alpha_1)`, computed from the sphere `a0` and final `h0 = alpha_1`
  tables. It is not an AANSS-page chart: it has already forgotten the AANSS
  filtration and assembled visible `a0` extensions. Black dots are cyclic
  factors in the table-level bottom-cell
  cokernel; hollow purple dots are cyclic factors in the shifted top-cell
  kernel. The dataset contains 451 records through the row-complete stem 153:
  236 bottom roles, 215 top roles, 420 finite factors of
  order 3, 20 of order 9, 7 of order 27, 2 of order 81, and 2 free
  `Z_(3)` factors. The short exact sequence between the bottom and top pieces
  can still be a nontrivial additive extension; both roles occur in 86
  bidegrees. Moreover, the C++ product
  writer's literal `o` tail can contain terms beyond its filtered precision;
  the converter discards it in the same table-level convention as Eva's
  `beta.py`. The chart therefore does not claim that these factors already
  determine the complete middle group.

The two plotted roles come from the cofiber long exact sequence

```text
0 -> coker(h0: E^{s-1,t-4}(S) -> E^{s,t}(S))
  -> E2^{s,t}(C alpha1)
  -> ker(h0: E^{s,t-4}(S) -> E^{s+1,t}(S)) -> 0.
```

Thus the bottom role stays in its sphere bidegree, while the top-kernel role
is displayed four stems to the right.

The raw Bockstein file prints a doubled/shifted single degree rather than the
usual `(stem, ANSS filtration)` pair. The Moore converter uses the grading
formula in `Boc.cpp` to restore standard coordinates. This is why the derived
M3 file should be used for an actual Moore `E2` generator chart.

To regenerate all four files from a local clone of `ANSS_data`, run:

```sh
python3 web/scripts/generate_web_data.py \
  /path/to/ANSS_data/data/185_BPAANSS_table.txt

python3 web/scripts/generate_web_data.py --no-products \
  /path/to/ANSS_data/data/185_BPBocSS_table.txt

python3 web/scripts/generate_m3_web_data.py \
  /path/to/ANSS_data/data/185_BPBocSS_table.txt

python3 web/scripts/generate_calpha1_web_data.py \
  /path/to/ANSS_data/data/185_BPAANSS_table.txt
```

The `C alpha_1` converter first uses the visible part of the `a0` table as the
triangular presentation `3e_i = sum_j a_ji e_j` for each sphere bidegree. It
then computes the exact finite kernel and cokernel within the resulting
truncated presentation of the homomorphism encoded by `h0`. Missing
near-cutoff operation rows are treated as unknown rather than zero; for the 185
run this makes stem 153 the maximal row-complete chart range. This range check
does not prove that every residual term of algebraic-Novikov filtration 40 or
higher vanishes. A direct calculation with the rank-two `BP_*BP` comodule for
`C alpha_1` is the definitive way to settle those filtered tails and the
remaining cross-cell additive extensions.

No further mathematics is needed to display the additive sphere spectral
sequence, the raw Bockstein pages, this one-copy additive M3 basis, or the
normalized `h0` and theta overlays. The raw `BocSS_a0` file is intentionally
excluded: multiplication by 3 on `E2_ANSS(M3)` is zero, while that large raw
table records 3-adic filtration and name-normalization data.

The remaining limitations are genuinely mathematical. The viewer does not
solve all extension data that assembles the sphere algebraic-Novikov `E∞`
graded pieces into ANSS `E2` groups; it does not decide whether missing
near-cutoff products are true zeroes; and it does not compute topological ANSS
differentials or hidden extensions for the sphere or M3.
