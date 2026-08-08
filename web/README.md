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

## Eva Belmont's 185 computation

The three checked-in 185 datasets are derived from the public text files in
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

The raw Bockstein file prints a doubled/shifted single degree rather than the
usual `(stem, ANSS filtration)` pair. The Moore converter uses the grading
formula in `Boc.cpp` to restore standard coordinates. This is why the derived
M3 file should be used for an actual Moore `E2` generator chart.

To regenerate all three files from a local clone of `ANSS_data`, run:

```sh
python3 web/scripts/generate_web_data.py \
  /path/to/ANSS_data/data/185_BPAANSS_table.txt

python3 web/scripts/generate_web_data.py --no-products \
  /path/to/ANSS_data/data/185_BPBocSS_table.txt

python3 web/scripts/generate_m3_web_data.py \
  /path/to/ANSS_data/data/185_BPBocSS_table.txt
```

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
