# DRAT proof certificates

Each subdirectory `n<N>_k<K>` set ships:

- `n<N>_k<K>.cnf` -- the CNF whose UNSAT proves a(N) >= K + 1.
- `n<N>_k<K>.drat` -- the DRAT proof emitted by cadical.
- `n<N>_k<K>.sidecar.json` -- SHA-256 of the CNF and DRAT, plus the verifier verdict (`s VERIFIED` from drat-trim).
- `n<N>_witness.json` -- the K-cell witness shell that gives a(N) <= K, paired with this UNSAT for a(N) = K + 1.

## Files omitted from this repo (n = 19, n = 20)

The raw DRAT proofs for n = 19 and n = 20 exceed GitHub's 100 MB per-file limit:

| n | k | DRAT size | Status |
|---|---|----------:|--------|
| 19 | 15 | ~162 MB | CNF + sidecar shipped; DRAT omitted |
| 20 | 15 | ~194 MB | CNF + sidecar shipped; DRAT omitted |

The sidecar JSON for each carries the SHA-256 hash of the original DRAT and the `s VERIFIED` verdict from `drat-trim` on the run host. To regenerate:

```
python ../../code/solve_truncsq_shell.py --n 19-20 --per-term-timeout 3600 \
    --emit-drat --check-drat --check-method drat
```

The same CNF -> DRAT -> drat-trim chain reproduces deterministically up to clause-ordering (cadical is sequential by default; passing `--threads=1` is sufficient).
