# OEIS -- Minimum Enclosing Shell on the Truncated-Square (4.8.8) Tiling

Solver code, DRAT proof certificates, geometric verifier, and publication figures for the new OEIS sequence introduced by this project.

## What is this sequence?

For an integer n >= 1, let a(n) be the minimum number of cells in a connected enclosing shell of an n-cell connected hole on the truncated-square (4.8.8) Archimedean tiling. The 4.8.8 tiling is composed of regular squares and regular octagons in a 1:1 ratio, with every vertex of degree 3 in the cell-adjacency graph. A connected enclosing shell is a connected set of cells, disjoint from the hole, that contains every cell edge-adjacent to the hole and topologically encloses it.

## Known terms (this work, machine-verified)

| n        | 1 | 2 | 3 | 4 | 5 | 6  | 7  | 8  | 9  | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 |
|:---:     |:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **a(n)** | **4** | **8** | **8** | **8** | **8** | **10** | **10** | **10** | **12** | **12** | **12** | **12** | **12** | **14** | **14** | **14** | **14** | **14** | **16** | **16** |

Each value carries a witness from exhaustive Cython Redelmeier enumeration of n-cell polyforms (with adaptive cascading upper bound on corona size) plus a machine-verified UNSAT certificate at k - 1 (DRAT, checked by `drat-trim`). Independent re-check on every witness by a pure-Python geometric verifier with a disjoint code path from the solver.

## Method

- **Witness (upper bound).** Cython Redelmeier enumeration walks all connected n-cell polyforms anchored on a finite BFS patch (radius 8) of the 4.8.8 tiling. For each polyform the corona size is evaluated, and the minimum across all polyforms is a(n). The framework is `sat_utils.frameworks.ShellSolverFramework` with `objective="enumeration"`.
- **Lower bound (DRAT).** A pure-PySAT three-partition (hole / shell / exterior) CNF encoder runs a CEGAR loop that adds connectivity cuts; once UNSAT is reached at k - 1, the augmented CNF and a DRAT proof are written to disk and `drat-trim` independently re-verifies the proof against the CNF.
- **Witness verifier.** A pure-Python geometric verifier rebuilds face adjacency from raw vertex-set intersection (a code path disjoint from the solver, no Cython, no SAT) and checks every reported (hole, shell) pair: hole and shell connected, corona contained in shell, sizes match.

## Key findings

- The +3 shell identity a(n) = (minimum perimeter)(n) + 3 that holds on the regular square (A283056) and regular hexagonal (A182619) grids does NOT extend to 4.8.8. A discrete Gauss-Bonnet argument shows that vertex degree 3 makes the corona of every connected hole connected (a necessary condition for shell == corona); the further claim that the minimum shell equals the corona is conjectural, not proved.
- Three structural conjectures match all 20 proved values (UNVERIFIED for n > 20):
  - C1: Corona-Equals-Shell on 4.8.8 (every connected hole H has minimum shell |C(H)|, with comps(H) = 1, bridge_count = 0, extra = 0).
  - C2: a(n) is non-decreasing in n.
  - C3: For n >= 3, a(n) - a(n - 1) is in {0, 2}; the +4 transition at n = 2 is unique to the leading edge.

## Running the solver

**Requirements.** Python 3.10+, python-sat (PyPI: `python-sat`), and the external binary `drat-trim`. No WSL or LRAT toolchain required.

```bash
# Witness + DRAT certificate for n = 1..20 (about 56 minutes total wall time
# on AMD Ryzen 5 5600, dominated by the n = 19..20 enumeration phases)
python code/solve_truncsq_shell.py --n 1-20 --per-term-timeout 3600 \
    --emit-drat --check-drat --check-method drat

# Independent witness verification (pure-Python, disjoint code path)
python code/verify_method1.py 20
```

## Files

| File | Description |
|------|-------------|
| `code/solve_truncsq_shell.py` | Primary solver (Cython Redelmeier enumeration + DRAT proof emission) |
| `code/verify_method1.py` | Independent geometric witness verifier (pure-Python) |
| `code/generate-figures.py` | Reproducible figure generator (Typst) |
| `research/solver-results.json` | Machine-readable witnesses + structural metadata |
| `research/solver-run-log.txt` | Solver stdout log |
| `research/verify_method1-results.json` | Geometric verifier results (every n PASS) |
| `research/drat/` | DRAT certificates per n |
| `research/drat-certification-summary.json` | Per-n `certified=true` summary |
| `submission/paper.pdf` | Standalone paper |
| `submission/truncsq-shell-figures.pdf` | Publication figures (data table + plateau chart) |
| `submission/oeis-draft.txt` | OEIS submission text |

## Prior art and acknowledgments

The +3 shell identity for the regular square grid is the Kamenetsky comment on OEIS A283056; the analogous identity for the regular hexagonal grid is A182619 (Pol). The minimum-perimeter polyomino sequence on the regular square grid is A027709. The 4.8.8 shell sequence is novel under the prior-art search recorded in this project (no OEIS match for the value prefix).

## Hardware

AMD Ryzen 5 5600 (6 cores, 12 threads), 16 GB RAM, Windows 11.

## License

[CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/) -- Peter Exley, 2026.

This work is freely available. If you find it useful, a citation or acknowledgment is appreciated but not required.
