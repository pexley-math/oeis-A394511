# OEIS A394511 -- Minimum Enclosing Shell on the Truncated-Square (4.8.8) Archimedean Tiling

Solver code and data for [OEIS A394511](https://oeis.org/A394511).

## The Problem

For an integer `n >= 1`, let `a(n)` be the minimum number of cells in a connected enclosing shell of an `n`-cell connected hole on the truncated-square (4.8.8) Archimedean tiling. The 4.8.8 tiling is composed of regular squares and regular octagons in a 1:1 ratio, with every vertex of degree 3 in the cell-adjacency graph (vertex configuration 4.8.8; symmetry group p4mm). An `n`-cell connected hole `H` is a connected set of `n` cells (squares or octagons). The corona `C(H)` is the set of cells edge-adjacent to `H` but not in `H`. A connected enclosing shell `S` is a connected superset of `C(H)`, disjoint from `H`, such that the cells outside `H union S` also form a connected set. `a(n)` is the minimum `|S|` over all valid `(H, S)`.

This is the truncated-square analog of [A283056](https://oeis.org/A283056) (square grid) and [A182619](https://oeis.org/A182619) (hexagonal grid). [A227004](https://oeis.org/A227004) is the coordination sequence for the same tiling but encodes a different "shell" notion (concentric coordination shells around a vertex), included here only to disambiguate.

## Results

**New proved terms (this work):**

| n | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **a(n)** | **4** | **8** | **8** | **8** | **8** | **10** | **10** | **10** | **12** | **12** | **12** | **12** | **12** | **14** | **14** | **14** | **14** | **14** | **16** | **16** |

Each value `a(n) = k + 1` is sandwich-proved by:

- **Upper bound:** a witness shell `S` with `|S| = k + 1` from a Cython implementation of Redelmeier's polyform enumeration on a finite BFS patch (radius 8) of the 4.8.8 tiling. The witness is independently re-checked by a pure-Python geometric verifier with a disjoint code path from the solver (vertex-intersection face adjacency, BFS connectivity, set-inclusion corona check; no SAT backend, no Cython enumerator, no shared imports). Verifier verdict: PASS for every `n = 1..20`.
- **Lower bound:** a `drat-trim`-certified UNSAT at `k` from a PySAT three-partition (hole / shell / exterior) CNF encoder under a CEGAR connectivity loop. Verdict `s VERIFIED` for every `n = 1..20`. The original DRAT proofs are not committed (see `research/drat/README.md`); the CNF + sidecar (with SHA-256 + verdict) are sufficient to regenerate and re-check.

## Conjecture

Three structural conjectures match all 20 proved values (UNVERIFIED for `n > 20`):

- **C1 (Corona-Equals-Shell on 4.8.8).** For every connected hole `H`, the minimum enclosing shell coincides with the corona, `|S| = |C(H)|`, with `comps(H) = 1`, `bridge_count = 0`, and `extra = 0` in the unified shell formula. A discrete Gauss-Bonnet argument shows that vertex degree 3 forces the corona of any connected hole to itself be connected (a necessary condition for shell == corona); the further claim that the minimum shell *equals* the corona is empirical.
- **C2 (Monotonicity).** `a(n)` is non-decreasing in `n`.
- **C3 (Plateau-and-jump cadence).** For `n >= 3`, `a(n) - a(n - 1)` is in `{0, 2}`. The unique `+4` transition `a(1) = 4 -> a(2) = 8` is structural to the leading edge: every 2-cell connected hole on 4.8.8 contains at least one octagon (no two squares are edge-adjacent), and the corona of a square plus an adjacent octagon has exactly 8 cells.

The `+3` shell identity that holds on the regular square grid (Kamenetsky comment on [A283056](https://oeis.org/A283056)) and the regular hexagonal grid ([A182619](https://oeis.org/A182619)) does NOT extend to the 4.8.8 tiling.

## Running the Solver

> **Note.** The scripts in `code/` are not runnable as-is from this repository alone. They import from a private shared-library monorepo (`sat_utils`, `figure_gen_utils`) that is not published here. The code is shipped as a reference for the method and for diff-style audit against the proof artefacts in `research/`. The proofs themselves -- the witness JSONs and the drat-trim `s VERIFIED` records in the sidecars -- are self-contained in `research/drat/` and can be re-verified with stock open-source binaries without running the solver.

**Requirements (for reference only):** Python 3.10+, `python-sat` (PySAT), the Cython enumerator from the private `sat_utils.tiling_enum` module, plus the external binary `drat-trim` for re-verification.

**Re-verifying any UNSAT lower bound from this repo alone:**

```bash
# Example: re-check the n = 6 lower bound (a(6) = 10 proved by UNSAT at k = 9).
# Two open-source binaries are needed: cadical (any 1.x or later) and drat-trim.
cadical research/drat/n6_k9.cnf --no-binary --proof n6_k9.drat --threads=1
drat-trim research/drat/n6_k9.cnf n6_k9.drat
# Expected: "s VERIFIED"
```

The same chain works for every `n` in 1..20. Approximate single-term wall time on a laptop: seconds for `n` in 1..10, minutes for 11..15, minutes-to-hours for 16..18, several hours each for `n = 19, 20`. See `research/drat/README.md` for the per-n file layout, the rationale for not shipping the original DRATs, and the witness specification.

**Example solver command (requires the private monorepo):**

```bash
# Witness + DRAT certificate for n = 1..20
python code/solve_truncsq_shell.py --n 1-20 --per-term-timeout 3600 \
    --emit-drat --check-drat --check-method drat

# Independent witness verification (pure-Python, disjoint code path)
python code/verify_method1.py 20
```

## Files

| File | Description |
|------|-------------|
| `code/solve_truncsq_shell.py` | Primary solver (reference) -- Cython Redelmeier enumeration + DRAT proof emission |
| `code/verify_method1.py` | Independent geometric witness verifier (reference, pure-Python, disjoint code path) |
| `research/solver-results.json` | Machine-readable witnesses + structural metadata for `n = 1..20` |
| `research/solver-run-log.txt` | Solver stdout log |
| `research/verify_method1-results.json` | Geometric verifier results (every `n` PASS) |
| `research/verify_method1-run-log.txt` | Geometric verifier run log |
| `research/drat/` | CNF, witness JSON, and sidecar (with SHA-256 + verdict) per `n`. DRATs are not committed; see folder README for regen and verify. |
| `submission/b394511.txt` | OEIS b-file (`n`, `a(n)`) for `n = 1..20` |

## Prior Art and Acknowledgments

The closest published analogs are [A283056](https://oeis.org/A283056) (square grid; the Kamenetsky comment proves the `+3` shell identity on the regular square grid) and [A182619](https://oeis.org/A182619) (hexagonal grid; analogous shell sequence). The present sequence is the truncated-square (4.8.8) analog. [A227004](https://oeis.org/A227004) is the coordination sequence for the same tiling but encodes a different concept (concentric coordination shells around a vertex), included here only as a disambiguation pointer.

This work was inspired by the [OEIS](https://oeis.org/) and the community of contributors who maintain it.

## Hardware

AMD Ryzen 5 5600 (6-core / 12-thread), 16 GB RAM, Windows 11.

## License

[CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/) -- Peter Exley, 2026.

This work is freely available. If you find it useful, a citation or acknowledgment is appreciated but not required.

## Links

- **A182619** (minimum enclosing shell on the hexagonal grid -- direct analog): https://oeis.org/A182619
- **A227004** (coordination sequence for the truncated-square 4.8.8 tiling -- different "shell" concept, disambiguation): https://oeis.org/A227004
- **A283056** (smallest polyomino admitting a hole of size n on the regular square grid -- direct analog with `+3` identity): https://oeis.org/A283056
- **A394511** (this sequence): https://oeis.org/A394511
