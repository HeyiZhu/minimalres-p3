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

## How `185_Calpha1_ANSS_E2.js` is constructed

### Inputs

The converter accepts either of the following equivalent inputs:

* `N_BPAANSS_table.txt`, stored beside files named exactly
  `N_BPAANSS_a0.txt` and `N_BPAANSS_h0.txt`; or
* an already generated `N_BPAANSS_table.js` payload whose `products` object
  contains the `a0` and `h0` table strings.

For the checked-in 185 data, the shortest reproducible command is:

```sh
python3 web/scripts/generate_calpha1_web_data.py \
  web/data/185_BPAANSS_table.js
```

This overwrites `web/data/185_Calpha1_ANSS_E2.js`.  The equivalent command
from Eva's raw files is:

```sh
python3 web/scripts/generate_calpha1_web_data.py \
  /path/to/ANSS_data/data/185_BPAANSS_table.txt
```

The leading `185_` supplies the declared internal-degree bound.  For an input
without a leading numerical bound, pass `--internal-degree-bound N`.
`--max-stem N` may lower, but not enlarge, the inferred row-complete range.
The other useful options are `--output-dir DIR` and `--source-url URL`; the
latter changes provenance metadata only.

### From algebraic-Novikov names to sphere groups

The source `BPAANSS_table` is not initially a list of independent generators
of the assembled sphere ANSS `E2` groups.  It is an algebraic-Novikov table.
The converter performs the following steps.

1. It discards rows containing `<-`, which are algebraic-Novikov
   differential pairs, and retains the singleton/permanent rows representing
   algebraic-Novikov `E∞` pieces.  In a name such as `[s-i]`, the leading
   integer is read as the actual ANSS filtration `s`.  In
   `|deg=(stem,q)`, the first coordinate is the stem and `q` is total
   algebraic-Novikov/Adams filtration.  The latter is used to order pieces,
   not as the final vertical chart coordinate.
2. It groups the surviving names by the true bidegree `(stem,s)`.
3. In each bidegree it interprets the `a0` rows as a triangular presentation

   ```text
   3 e_source = sum_j c_j e_target_j.
   ```

   Repeated target names encode coefficients modulo 3.  Every target is
   required to remain in the same sphere bidegree and to have strictly higher
   total algebraic-Novikov filtration.  Carrying base-3 digits through these
   relations assembles the displayed associated-graded pieces into the
   finite, truncated 3-primary abelian group in that bidegree.
4. It treats the `h0` table as a homomorphism of bidegree
   `(stem,s) -> (stem+3,s+1)`.  It checks this degree on every target and also
   checks that `h0` respects all of the `a0` relations.  A missing operation
   row is an error/unknown, not a zero product.

Names in these tables are treated as opaque identifiers.  On an operation
right-hand side, three repeated copies cancel and two copies mean coefficient
2 modulo 3.

### Taking the two-cell Atiyah--Hirzebruch homology

For `C alpha_1 = S^0 union_{alpha_1} e^4`, cell filtration gives two shifted
copies of the assembled sphere groups and the only cellular differential is
Yoneda multiplication by `h0 = alpha_1`.  The converter therefore computes:

* at target sphere bidegree `(n,s)`, the cyclic invariant factors of
  `coker[h0:E(n-3,s-1) -> E(n,s)]`, emitted as bottom-cell roles at `(n,s)`;
* at source sphere bidegree `(n,s)`, the cyclic invariant factors of
  `ker[h0:E(n,s) -> E(n+3,s+1)]`, emitted as top-cell roles at the shifted
  cofiber position `(n+4,s)`.

For the finite groups in this dataset, the script enumerates elements in the
triangular presentation, forms the exact kernel, image and quotient there,
computes cyclic invariant factors, and chooses representatives by
backtracking.  The invariant factors are intrinsic to the truncated
subquotient; the chosen representatives are not canonical.  This exhaustive
method is practical here because every bidegree is small, but its cost is
exponential in the number of algebraic-Novikov pieces in one bidegree.

The unit bidegree is the one free case and is handled explicitly.  Since

```text
h0 : Z_(3){1} -> Z/3{alpha_1}
```

is onto, the output contains a bottom `Z_(3)` at `(0,0)`, no bottom
`alpha_1` at `(3,1)`, and the free kernel
`3 Z_(3) ~= Z_(3)` as a top role at `(4,0)`.

This calculation produces the cell-filtration associated graded

```text
bottom = coker(h0),       top = ker(h0)[4].
```

It does not choose a splitting or solve the possible additive extension
between the two roles.  It also does not compute products on `C alpha_1`.

### Range and precision checks

The converter refuses to use an `h0` source whose row is absent or whose
internal degree is too close to the declared input bound for its degree-4
target.  It also refuses bidegrees with incomplete `a0` presentations.  The
first such obstruction in Eva's 185 data makes stem 153 the largest
rectangular row-complete range; requesting `--max-stem 154` fails instead of
silently treating the missing information as zero.

There is a second, genuinely mathematical precision warning.  Eva's C++
writer appends the literal target `o` after it stops recovering names at its
algebraic-Novikov filtration cutoff.  The converter drops `o`, following the
table-level convention in `beta.py`, but an `o` can hide a residual term at
filtration 40 or above.  Therefore “row-complete through stem 153” is relative
to the internal-degree-185 and filtration-40 files; it is not a proof that all
higher-filtered tails vanish.

### What the Python emits and what actually draws the chart

`generate_calpha1_web_data.py` does **not** draw SVG.  It serializes a browser
payload of the form:

```js
globalThis.MINIMALRES_DATA = {
  name: "...",
  kind: "two-cell",
  cellLabels: { bottom: "...", top: "..." },
  text: "...one record per cyclic factor...",
  products: {}
};
```

A typical record in `text` has the line-oriented schema:

```text
calpha1_b_11_1_1 |deg=(11,1) |cell=bottom |piece=coker(h0)
  |group=Z/9 |representative=v0^1[1-1] |sphere=(11,1)
  |cell-extension=unresolved |filtered-tail=discarded
```

The real file stores each record on one line.  The additional metadata at the
payload level records counts, provenance and range qualifications, although
the current UI does not display all of those fields.

When the browser opens
`?data=185_Calpha1_ANSS_E2`, `app.js` loads
`data/185_Calpha1_ANSS_E2.js`, parses `|deg=(stem,s)` as the coordinates and
`|cell=...` as the visual role, and renders circles into the page's SVG:

* bottom roles are filled black;
* top roles are hollow purple;
* multiple cyclic factors in one bidegree receive small horizontal pixel
  offsets, which are visual separation only and do not change their grading;
* `kind: "two-cell"` supplies the fixed `ANSS E2` page selector and shows the
  data-specific cell legend.

The dot shape does not encode `Z/3`, `Z/9`, and so on.  Click a dot again to
open its details and read the raw `|group=` and `|representative=` fields.
The generic popup's short “Generator” and “Coefficient” fields are not useful
for the synthetic `calpha1_b_...` identifiers; the raw record is authoritative.

Because the payload has `products: {}` and contains no `<- ... |dN` records,
the normalized `C alpha_1` chart draws neither products nor differentials.
In particular, it does not draw the cellular `h0` arrows: the Python program
has already taken their kernel/cokernel homology.

### Verification

Run the focused regression suite after changing the importer or algorithm:

```sh
python3 -m unittest web/scripts/test_generate_calpha1_web_data.py
```

It checks a synthetic nontrivial `Z/9 -> Z/3` example, coefficients modulo 3,
the low-stem long-exact-sequence checks, the full 185 counts and invariant
orders, rejection of stem 154, and truncation by `--max-stem`.  At the time of
this writing, regenerating from the checked-in sphere JS reproduces the
checked-in `185_Calpha1_ANSS_E2.js` byte for byte.

The complete local smoke test is:

```sh
python3 web/scripts/generate_calpha1_web_data.py \
  web/data/185_BPAANSS_table.js
python3 -m unittest web/scripts/test_generate_calpha1_web_data.py
cd web
python3 -m http.server 4173
```

Then open
`http://localhost:4173/?data=185_Calpha1_ANSS_E2` in a browser.

## Generalizing the two-cell workflow

Let `C(f) = S^0 union_f e^d`, where `f:S^{d-1}->S^0`.  The correct backend
depends on the Adams--Novikov filtration of `f`; there is not one uniform
kernel/cokernel recipe for every two-cell complex.

| AN filtration of `f` | What `BP_*C(f)` remembers | Appropriate workflow |
| --- | --- | --- |
| 0, for example `3^k` | A coefficient quotient such as `BP_*/(3^k)`, not a free rank-two extension | Use a coefficient Bockstein or a direct torsion-comodule resolver.  `generate_m3_web_data.py` is the separate `M(3)` backend. |
| 1 | A non-split rank-two `BP_*BP`-comodule extension classified by an Ext-1 class `x_f` | Two sphere `E2` copies with cellular `d1=x_f`; compute bottom `coker(x_f)` and shifted top `ker(x_f)`.  This is the reusable part of the present `C alpha_1` generator. |
| `r >= 2`, for example `beta_1` with `r=2` | The ordinary rank-two comodule is split and has forgotten the attachment | Additively, `E2(C(f))` is two shifted sphere copies.  The attachment first appears later as a topological `d_r` on the top-cell unit; displaying/computing it requires a filtered chain map or Yoneda `r`-extension and its mapping cone. |

For another filtration-one attachment, the reusable mathematical input is an
actual multiplication/connecting-map table for `x_f` of bidegree
`(d-1,+1)`.  The cell dimension alone is not enough.  A first refactor of the
current program should parameterize:

* the prime and coefficient relation (`3` and `a0` are now hard-coded);
* the operation table/name and its bidegree (`h0`, `(+3,+1)`);
* the top-cell shift (`+4` stems);
* output identifiers, labels and provenance;
* the unit/free-summand behavior; and
* cutoff loss determined by the operation's degree.

For a durable generic implementation, separate the following layers rather
than copying and editing the `C alpha_1` script for every example:

1. an assembled graded sphere-`E2` presentation, with generators, relations,
   free rank, provenance and completeness status;
2. a graded operation object containing its bidegree, matrices, convention,
   and row status (`complete`, `missing`, or filtered residual);
3. a two-cell specification containing `d`, the attaching filtration, and the
   selected backend (`coefficient Bockstein`, `Ext-1 kernel/cokernel`, or
   `split E2 plus filtered cone`);
4. exact kernel/cokernel algebra for finitely presented `Z_(p)`-modules,
   preferably matrix/Smith-normal-form based rather than exhaustive element
   enumeration;
5. a range certificate that propagates every missing row and filtered tail;
   and
6. a chart-data adapter that emits the current `|deg`, `|cell`, `|group` line
   schema for backward compatibility.

Even for filtration-one attachments, the cell-crossing additive extension,
unrecorded filtered tails, and inherited products on the cofiber remain extra
mathematical problems.  For filtration at least two, substituting a beta
product table into this kernel/cokernel generator would compute the wrong
object: a filtered chain-level cone is the missing structure.

## Regenerating the other 185 datasets

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

## Remaining viewer limitations

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
