# OEIS A394511 -- Minimum Enclosing Shell on the Truncated-Square (4.8.8) Archimedean Tiling

Solver code and data for [OEIS A394511](https://oeis.org/A394511).

## The Problem

For `n >= 1`, `a(n)` is the smallest number of cells in a connected ring (a "shell") that completely encloses a connected `n`-cell hole on the truncated-square (4.8.8) Archimedean tiling. The 4.8.8 tiling is made of regular squares and regular octagons in a 1:1 ratio; every vertex has degree 3, and the symmetry group is `p4mm`.

Precisely: a hole `H` is a connected set of `n` cells (squares or octagons). The corona `C(H)` is the set of cells edge-adjacent to `H` but not in `H`. A shell `S` is a connected superset of `C(H)`, disjoint from `H`, such that the cells outside `H union S` also form a connected set. `a(n) = min |S|`.

This is the truncated-square analog of [A283056](https://oeis.org/A283056) (square grid) and [A182619](https://oeis.org/A182619) (hexagonal grid). [A227004](https://oeis.org/A227004) is the coordination sequence on the same tiling -- a different "shell" notion, included only as a disambiguation pointer.

## Results

**New proved terms (this work):**

| n | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **a(n)** | **4** | **8** | **8** | **8** | **8** | **10** | **10** | **10** | **12** | **12** | **12** | **12** | **12** | **14** | **14** | **14** | **14** | **14** | **16** | **16** |

Each value `a(n) = k + 1` is proved both ways:

- **Upper bound (`a(n) <= k + 1`).** An exhaustive computer search over all connected `n`-cell holes on a finite patch of the tiling (radius 8) finds at least one hole whose corona has size `k + 1`.
- **Lower bound (`a(n) >= k + 1`).** A SAT solver proves that no valid hole-shell pair with shell of size at most `k` exists. The machine-checkable proof certificate is independently re-verified by `drat-trim` (verdict `s VERIFIED` on every term).
- **Cross-check.** Every upper-bound witness is independently re-checked by a separate pure-Python geometric verifier with a disjoint code path: PASS for every `n = 1..20`.

## Conjecture

Three structural conjectures match all 20 proved values (UNVERIFIED for `n > 20`):

- **C1 (Corona-Equals-Shell on 4.8.8).** For every connected hole `H`, the minimum enclosing shell equals the corona itself: `|S| = |C(H)|`. Half of this is forced by the geometry: every vertex of the 4.8.8 tiling has degree 3, which implies the corona of any connected hole is connected (a necessary condition for "shell equals corona"). The rest -- that the corona is also *sufficient* and no smaller shell exists -- is empirical for `n = 1..20`.
- **C2 (Monotonicity).** `a(n)` is non-decreasing.
- **C3 (Plateau-and-jump cadence).** For `n >= 3`, `a(n) - a(n - 1)` is in `{0, 2}`: the sequence either stays flat or jumps by exactly 2. The unique `+4` step `a(1) = 4 -> a(2) = 8` is special to the leading edge -- every 2-cell connected hole on 4.8.8 contains at least one octagon (no two squares are edge-adjacent), and the corona of a square plus an adjacent octagon has exactly 8 cells.

## Running the Solver

> **Note.** The scripts in `code/` are not runnable as-is. They import from a private shared-library monorepo (`sat_utils`, `figure_gen_utils`) that is not published here and are shipped only as a reference for the method. The proofs themselves -- in `research/drat/` (CNF + witness JSON + sidecar) -- are self-contained and re-verifiable with two stock open-source binaries.

**Re-verifying any lower bound from this repo alone:**

```bash
# Example: re-check the n = 6 lower bound (a(6) = 10, proved by UNSAT at k = 9).
cadical research/drat/n6_k9.cnf --no-binary --proof n6_k9.drat --threads=1
drat-trim research/drat/n6_k9.cnf n6_k9.drat
# Expected: "s VERIFIED"
```

The same chain works for every `n` in 1..20. Approximate single-term wall time on a laptop: seconds for `n` in 1..10, minutes for 11..15, minutes to about an hour for 16..18, several hours each for `n = 19, 20`. See `research/drat/README.md` for the per-`n` file layout, the rationale for not shipping the original DRAT files, and the witness specification.

## Files

| File | Description |
|------|-------------|
| `code/solve_truncsq_shell.py` | Primary solver (reference) |
| `code/verify_method1.py` | Independent geometric witness verifier (reference) |
| `research/solver-results.json` | Witnesses and structural metadata for `n = 1..20` |
| `research/solver-run-log.txt` | Solver stdout log |
| `research/verify_method1-results.json` | Geometric verifier results (every `n` PASS) |
| `research/verify_method1-run-log.txt` | Geometric verifier run log |
| `research/drat/` | CNF, witness JSON, and sidecar per `n`. DRATs not committed; see folder README. |
| `submission/b394511.txt` | OEIS b-file (`n`, `a(n)`) for `n = 1..20` |

## Prior Art and Acknowledgments

The closest published analogs are [A283056](https://oeis.org/A283056) (square grid) and [A182619](https://oeis.org/A182619) (hexagonal grid). [A227004](https://oeis.org/A227004) is the coordination sequence on the same tiling -- a different "shell" concept included only as a disambiguation pointer.

This work was inspired by the [OEIS](https://oeis.org/) and the community of contributors who maintain it.

## Hardware

AMD Ryzen 5 5600 (6-core / 12-thread), 16 GB RAM, Windows 11.

## License

[CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/) -- Peter Exley, 2026.

This work is freely available. If you find it useful, a citation or acknowledgment is appreciated but not required.

## Links

- **A182619** (minimum enclosing shell on the hexagonal grid): https://oeis.org/A182619
- **A227004** (coordination sequence for the truncated-square 4.8.8 tiling -- different concept): https://oeis.org/A227004
- **A283056** (smallest polyomino admitting a hole of size n on the square grid): https://oeis.org/A283056
- **A394511** (this sequence): https://oeis.org/A394511
