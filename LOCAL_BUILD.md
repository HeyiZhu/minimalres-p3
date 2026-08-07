# Local build and sphere ANSS computation

This project computes at the prime 2.  A C++ compiler, CMake, and GMP are
required.  OpenMP is optional: if it is unavailable CMake builds a slower,
serial version.

## Build

From the repository root:

```sh
cmake -S . -B build-local -DCMAKE_BUILD_TYPE=Release
cmake --build build-local --parallel
```

The sphere computation uses these executables:

- `mr_st`: minimal resolution over the mod-2 Steenrod algebra;
- `BPtab`: truncated BP Hopf-algebroid structure tables;
- `mr_BP`: BP resolution, algebraic Novikov and Bockstein tables.

## Run

Run each computation in its own directory because output names are derived
only from the degree cutoff.  For internal degree cutoff `D` and desired BP
resolution length `L`, `mr_st` must be run through `L+1` (the BP lift uses the
next modeled generator set):

```sh
mkdir run-d20-l4
cd run-d20-l4
../build-local/mr_st 20 5
../build-local/BPtab 20
../build-local/mr_BP 20 4
```

Using the same value of `L` for `mr_st` and `mr_BP` can access a nonexistent
`i+1` generator set in the legacy code.  Larger cutoffs grow rapidly.  A low
degree cutoff can also be too small for the optional theta multiplication
tables; an `out of range for thetaN` message at the end does not invalidate
the ANSS table.

## Main output

For `D=20`, the most useful human-readable files are:

- `20_BPAANSS_table.txt`: algebraic Novikov spectral sequence entries;
- `20_BPBocSS_table.txt`: 2-adic/Bockstein refinement;
- `20_BPAANSS_h0.txt`: multiplication by the 2-extension (`h0`/`v0`);
- `20_BPB2A_table.txt`: correspondence from Bockstein names to algebraic
  Novikov names;
- `20_BPBocSS_thetaN.txt`: selected top-theta multiplication tables.

Files ending in `_binary`, plus `maps`, `gens`, `res`, `cpx`, and the matrix
files, are machine-readable intermediate/checkpoint data used by later stages.

An algebraic Novikov line such as

```text
v0^1[2-3] <- [1-3] |d2 |deg=(14,3)
```

records a differential from the class on the right to the class on the left.
`d2` is the differential length used by this table.  In `[s-i]`, `s` is the
resolution (cobar/Ext) degree and `i` identifies a chosen generator in that
resolution degree.  A prefix `v0^a v1^b ...` is the BP-coefficient monomial.
For the AANSS table, `deg=(x,y)` is printed as

```text
x = 2t-s,   y = s + (algebraic Novikov filtration).
```

Thus the first coordinate is the stem convention used by the program and the
second is the total displayed filtration.  A line without an arrow is an
untagged class at the computed page/truncation.  The table is truncated data,
so absence beyond the requested degree or resolution length is not a
vanishing statement.

The Bockstein table uses the same class notation but prints a single internal
degree (`|deg=n`).  Its `d0`, `d1`, ... labels belong to the Bockstein
filtration convention and should not be confused directly with ANSS page
numbers.
