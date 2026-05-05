# Proof certificates

For each n in 1..20 this directory holds the inputs needed to verify
the proof that a(n) = K + 1, where K is the integer in the filename:

- `n<N>_k<K>.cnf` -- the CNF whose UNSAT establishes a(N) >= K + 1.
- `n<N>_witness.json` -- a witness shell of size a(N) = K + 1.
  Combined with the UNSAT at K this gives a(N) = K + 1.
- `n<N>_k<K>.sidecar.json` -- SHA-256 of the CNF, SHA-256 of the
  original DRAT produced on the run host, and the `s VERIFIED`
  verdict from `drat-trim` checking that DRAT against the CNF.

## Why are no .drat files shipped?

A DRAT proof is reproducible from the CNF: run any DRAT-emitting SAT
solver, then check the result with `drat-trim`. The CNF is the
load-bearing artefact; one DRAT is as good as another for proving the
same UNSAT. Shipping the original DRATs would add ~500 MB to the repo
without changing what can be verified, so they are deliberately
omitted.

The sidecar's SHA-256 of the original DRAT lets a reviewer who reruns
cadical with the same version + `--threads=1` confirm bit-for-bit
reproducibility against our run-host artefact, if desired.

## How to regenerate and verify any term

Two open-source binaries are needed: `cadical` (any 1.x or later
release) and `drat-trim`. From this directory:

    cadical n<N>_k<K>.cnf --no-binary --proof n<N>_k<K>.drat --threads=1
    drat-trim n<N>_k<K>.cnf n<N>_k<K>.drat

`drat-trim` prints `s VERIFIED` on success.

Approximate single-term runtimes on a laptop:

| n | wall time |
|---|---|
| 1..10 | seconds |
| 11..15 | minutes |
| 16..18 | minutes to ~1 hour |
| 19..20 | several hours each |

## Verifying the witness side independently

`n<N>_witness.json` carries the integer cell IDs for `hole_cells` and
`shell_cells` on the truncated-square (4.8.8) tiling at radius 8.
Any tool that reconstructs the cell-adjacency graph from cell vertex
sets and checks the four conditions

1. `hole` is edge-connected,
2. `shell` is edge-connected and disjoint from `hole`,
3. every cell edge-adjacent to `hole` is in `shell` (corona inclusion),
4. `|shell| = a(N)`,

certifies a(N) <= a(N), giving the upper-bound half of the sandwich.
The geometric specification of the 4.8.8 tiling is in the project
README and paper.
