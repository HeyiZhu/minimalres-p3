# Local p=3 build and smoke test

This branch is the prime-3 fork.  The sphere pipeline uses `mr_st`, `BPtab`,
and `mr_BP`, in that order.  GMP is required; OpenMP is optional and is omitted
by the serial macOS commands below.

## Build on Apple silicon

```sh
mkdir -p build-p3

c++ -std=c++11 -O2 -I. \
  exponents.cpp Fp.cpp mon_index.cpp steenrod.cpp steenrod_init.cpp stmain.cpp \
  -o build-p3/mr_st

c++ -std=c++11 -O2 -I. \
  Z3.cpp mon_index.cpp BP.cpp BPQ.cpp BPtable.cpp exponents.cpp Qp.cpp Fp.cpp \
  -L/usr/local/lib -lgmpxx -lgmp -o build-p3/BPtab

c++ -std=c++11 -O2 -I. \
  BPcomplex.cpp streams.cpp algNov.cpp Boc.cpp multiplication.cpp exponents.cpp \
  Fp.cpp mon_index.cpp Z3.cpp BP.cpp BP_init.cpp BPmain.cpp \
  -L/usr/local/lib -lgmpxx -lgmp -o build-p3/mr_BP
```

## Small sphere example

The first argument is the program's half-degree cutoff.  To compute the BP
resolution through filtration `L`, the Steenrod resolution must be computed
through `L+1`.

```sh
mkdir -p run-p3-d10-l2
cd run-p3-d10-l2
../build-p3/mr_st 10 3
../build-p3/BPtab 10
../build-p3/mr_BP 10 2
```

Each stage should print `Fp operations initialized with p=3`.

The principal outputs are `10_BPAANSS_table.txt` (algebraic Novikov spectral
sequence), `10_BPBocSS_table.txt` (3-adic Bockstein table), and their `_binary`
checkpoint forms.  At this small cutoff the AANSS table is

```text
[0-0]       |deg=(0,0)
v0^1[0-0]   |deg=(0,1)
[1-0]       |deg=(3,1)
```

These are the unit, its first 3-adic (`v0`) multiple, and the first
filtration-one class in stem 3 (the location of the prime-3 alpha-one class).
The output is truncated: absence beyond the cutoff is not a vanishing claim.
An `out of range for beta1` message from the optional multiplication stage is
expected at this deliberately small degree and does not invalidate the ANSS
or Bockstein tables.

## Larger sphere chart and the two-cell complex C(alpha1)

At the prime 3, the class called `h0` by this program is

```text
(eta_R(v1) - eta_L(v1))/3
```

in Adams--Novikov bidegree `(stem, filtration) = (3, 1)`.  It detects the
stable element `alpha1 : S^3 -> S^0`.  Its cofiber is denoted consistently by
`C(alpha1) = S^0 union_{alpha1} e^4`.

The following computes a larger sphere example through half-degree 40 and
resolution length 8.  The Steenrod resolution must be one step longer.

```sh
mkdir -p run-p3-d40-l8
cd run-p3-d40-l8
../build-p3/mr_st 40 9
../build-p3/BPtab 40
../build-p3/mr_BP 40 8
cd ..
```

Generate browser data from the resulting tables:

```sh
python3 web/scripts/generate_web_data.py \
  run-p3-d40-l8/40_BPAANSS_table.txt \
  run-p3-d40-l8/40_BPBocSS_table.txt
python3 -m http.server 4173 --directory web
```

Open the sphere chart at
`http://localhost:4173/index.html?data=40_BPAANSS_table`, the two-cell AHSS
page at `http://localhost:4173/index.html?data=40_BPCAlpha1_AHSS`, and the
result after taking the attaching-map homology at
`http://localhost:4173/index.html?data=40_BPCAlpha1_AANSS_E2`.

The `C(alpha1)` AHSS chart is assembled from two shifted copies of the computed
sphere AANSS and `40_BPAANSS_h0.txt`.  Its top-cell copy is shifted by four
stems, and its attaching differential sends `top(x)` to `bottom(h0*x)`.  The
separate `CAlpha1_AANSS_E2` data takes kernel on the top cell and cokernel on
the bottom cell over `F3`, bidegree by bidegree.  At truncation boundaries it
only reports bidegrees for which every required `h0` value was computed.  This
is still an AHSS-derived calculation rather than a direct resolution of the
`BP_*BP` comodule `BP_*C(alpha1)`.
