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

