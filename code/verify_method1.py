"""
verify_method1.py -- independent geometric witness verifier for the
truncated-square (4.8.8) shell minimisation problem.

Purpose
-------
Given the solver's reported (hole_cells, shell_cells, value) for each
proved n, certify the SAT/witness side of the proof: confirm that the
witness (H, S) is a valid hole-shell pair on the truncated-square
(4.8.8) tiling achieving |S| = value. Any single bug in the solver's
encoding (wrong adjacency, wrong connectivity, missing corona cell,
double-counted shell cell) is caught here before /solver-iterate.

This verifier proves a(n) <= value (upper bound). The complementary
lower bound a(n) >= value is established by /solver-iterate: for
``objective="enumeration"`` the lower bound is justified by the
exhaustive Cython Redelmeier walk over all n-cell connected polyforms
on a sufficient-radius patch (PROVED status; no DRAT cert because no
SAT call). The verifier here is therefore the SECOND independent
proof path -- pure-Python adjacency reconstruction + BFS -- and the
enumeration objective is the FIRST proof path inside the solver.

Disjointness from the solver
----------------------------
Solver path: ShellSolverFramework(objective="enumeration") -> Cython
  Redelmeier (sat_utils.tiling_enum) + bridge-gap shell evaluator.
This verifier:
  - No SAT/CP-SAT backend; pure Python set/BFS operations.
  - No imports from solve_*.py, sat_utils.frameworks, sat_utils.tiling_enum,
    or sat_utils.tiling_shell.
  - Independent face-adjacency reconstruction from raw vertex
    coincidence on the truncated-square fundamental domain. Even if
    the shared sat_utils.tilings.truncsq.build_tiling produced a wrong
    cell_adj, this verifier would not propagate the bug because it
    rebuilds adjacency from cell vertex sets only.
  - Inherits VerifierBase scaffold (argparse, per-n loop, exit code)
    -- the two-verifier rule explicitly permits a shared
    UI/orchestration surface (sat_utils/verifier_base.py docstring).

What it verifies for each n
---------------------------
1. solver-results entry exists with status PROVED.
2. hole_cells and shell_cells parse into the cell index space.
3. |hole| == n.
4. hole and shell are disjoint.
5. hole is edge-connected under independently-reconstructed cell_adj.
6. shell is edge-connected under independently-reconstructed cell_adj.
7. corona(hole) := neighbours(hole) \\ hole is a subset of shell.
   (Every cell adjacent to a hole cell is in the shell.)
8. |shell| == value.

If all eight pass, the witness establishes a(n) <= value. If any fail,
the verifier reports FAIL with a specific diagnosis.

Outputs
-------
research/verify_method1-results.json (via figure_gen_utils.save_versioned)
research/verify_method1-run-log.txt   (via figure_gen_utils.save_versioned)

Usage
-----
    python verify_method1.py            # uses default_max_n
    python verify_method1.py 13         # max_n=13
    python verify_method1.py --n 3      # single n
    python verify_method1.py --per-term-timeout 600
    python verify_method1.py --no-timeout

Exit code: 0 iff every proved n passes within the per-term budget.
"""

import json
import os
import sys
import time
from collections import defaultdict, deque
from datetime import datetime

_PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_SHARED = os.path.abspath(os.path.join(_PROJECT_DIR, ".."))
if _SHARED not in sys.path:
    sys.path.insert(0, _SHARED)

try:
    from figure_gen_utils.pipeline_timeouts import VERIFIER_TIMEOUT_S
except ImportError:
    VERIFIER_TIMEOUT_S = 3600

from sat_utils.tilings.truncsq import build_tiling
from sat_utils.verifier_base import VerifierBase
from figure_gen_utils.solver_log import STATUS_PROVED, STATUS_TIMEOUT


_RESULTS_PATH = os.path.join(_PROJECT_DIR, "research", "solver-results.json")
_TILING_RADIUS = 8  # must match the solver's tiling_radius.


def _independent_cell_adj(cells):
    """Rebuild cell-cell face adjacency from vertex sets ONLY.

    Two cells are adjacent iff their vertex sets share exactly two
    vertices (one shared edge). This is a different code path from the
    edge-set lookup in sat_utils.tilings.truncsq.build_tiling: that
    path uses ``edge_to_cells[frozenset(...)]`` indexed off the
    pre-built edge set; this path uses raw vertex-set intersection.
    """
    vsets = {cid: set(info["vertices"]) for cid, info in cells.items()}
    by_vertex = defaultdict(list)
    for cid, vs in vsets.items():
        for v in vs:
            by_vertex[v].append(cid)
    adj = defaultdict(set)
    seen = set()
    for v, cids in by_vertex.items():
        for i in range(len(cids)):
            a = cids[i]
            for j in range(i + 1, len(cids)):
                b = cids[j]
                key = (a, b) if a < b else (b, a)
                if key in seen:
                    continue
                seen.add(key)
                shared = vsets[a] & vsets[b]
                if len(shared) == 2:
                    adj[a].add(b)
                    adj[b].add(a)
    return dict(adj)


def _bfs_connected(cells_set, adj):
    """Return True iff the given cell set is non-empty and connected."""
    if not cells_set:
        return False
    start = next(iter(cells_set))
    seen = {start}
    q = deque([start])
    while q:
        c = q.popleft()
        for nb in adj.get(c, ()):
            if nb in cells_set and nb not in seen:
                seen.add(nb)
                q.append(nb)
    return seen == cells_set


def _parse_cells(raw_list):
    """Coerce a list of cell-ID strings/ints to a set of ints."""
    out = set()
    for c in raw_list or ():
        try:
            out.add(int(c))
        except (TypeError, ValueError):
            return None
    return out


# Cache the (cells, adj) pair across verify_n calls -- rebuilding the
# radius-8 tiling is cheap but unnecessary per term.
_TILING_CACHE = {}


def _get_tiling(radius):
    if radius in _TILING_CACHE:
        return _TILING_CACHE[radius]
    _verts, _edges, _v_adj, cells, _shared_cell_adj = build_tiling(
        radius=radius)
    indep_adj = _independent_cell_adj(cells)
    _TILING_CACHE[radius] = (cells, indep_adj)
    return cells, indep_adj


def verify_witness(n, solver_results, deadline=None):
    """Validate the (hole, shell) witness for a single n.

    Returns a dict with keys:
      n, ok (bool), status, detail, elapsed,
      hole_size, shell_size, corona_size.
    """
    t0 = time.time()
    rec = {
        "n": n, "ok": False, "status": "FAIL", "detail": "",
        "elapsed": 0.0, "hole_size": 0, "shell_size": 0,
        "corona_size": 0,
    }
    key = str(n)
    if key not in solver_results:
        rec["detail"] = f"n={n}: no entry in solver-results.json"
        rec["elapsed"] = time.time() - t0
        return rec

    res = solver_results[key]
    if res.get("status") != STATUS_PROVED:
        rec["detail"] = (
            f"n={n}: solver status is {res.get('status')!r}, not PROVED"
        )
        rec["elapsed"] = time.time() - t0
        return rec

    reported = res.get("value")
    hole = _parse_cells(res.get("hole_cells"))
    shell = _parse_cells(res.get("shell_cells"))
    if hole is None or shell is None:
        rec["detail"] = f"n={n}: hole_cells/shell_cells malformed"
        rec["elapsed"] = time.time() - t0
        return rec

    rec["hole_size"] = len(hole)
    rec["shell_size"] = len(shell)

    if len(hole) != n:
        rec["detail"] = f"n={n}: |hole|={len(hole)} but n={n}"
        rec["elapsed"] = time.time() - t0
        return rec

    if len(shell) != reported:
        rec["detail"] = (
            f"n={n}: reported value={reported} but |shell|={len(shell)}"
        )
        rec["elapsed"] = time.time() - t0
        return rec

    if hole & shell:
        rec["detail"] = (
            f"n={n}: hole and shell overlap on "
            f"{sorted(hole & shell)[:5]}"
        )
        rec["elapsed"] = time.time() - t0
        return rec

    cells, adj = _get_tiling(_TILING_RADIUS)

    missing = (hole | shell) - cells.keys()
    if missing:
        rec["detail"] = (
            f"n={n}: cells {sorted(missing)[:5]} are outside the "
            f"radius-{_TILING_RADIUS} tiling"
        )
        rec["elapsed"] = time.time() - t0
        return rec

    if deadline is not None and time.time() >= deadline:
        rec["status"] = STATUS_TIMEOUT
        rec["detail"] = f"n={n}: timeout before connectivity check"
        rec["elapsed"] = time.time() - t0
        return rec

    if not _bfs_connected(hole, adj):
        rec["detail"] = f"n={n}: hole is not edge-connected"
        rec["elapsed"] = time.time() - t0
        return rec

    if not _bfs_connected(shell, adj):
        rec["detail"] = f"n={n}: shell is not edge-connected"
        rec["elapsed"] = time.time() - t0
        return rec

    if deadline is not None and time.time() >= deadline:
        rec["status"] = STATUS_TIMEOUT
        rec["detail"] = f"n={n}: timeout before corona check"
        rec["elapsed"] = time.time() - t0
        return rec

    corona = set()
    for c in hole:
        for nb in adj.get(c, ()):
            if nb not in hole:
                corona.add(nb)
    rec["corona_size"] = len(corona)

    missing_in_shell = corona - shell
    if missing_in_shell:
        rec["detail"] = (
            f"n={n}: corona cells {sorted(missing_in_shell)[:5]} are "
            f"NOT in the shell ({len(missing_in_shell)} missing)"
        )
        rec["elapsed"] = time.time() - t0
        return rec

    rec["ok"] = True
    rec["status"] = "PASS"
    rec["detail"] = (
        f"n={n}: hole connected (|H|={n}), shell connected "
        f"(|S|={len(shell)}={reported}), corona ({len(corona)} cells) "
        f"contained in shell"
    )
    rec["elapsed"] = time.time() - t0
    return rec


def _write_outputs(records, project_dir, all_pass, cli_args):
    from figure_gen_utils.versioned_output import save_versioned
    research_dir = os.path.join(project_dir, "research")
    os.makedirs(research_dir, exist_ok=True)

    summary = {
        "verifier": "verify_method1",
        "method": (
            "geometric witness verification on the truncated-square "
            "(4.8.8) tiling: independent vertex-intersection face "
            "adjacency, BFS connectivity, set-inclusion corona check "
            "(pure Python, no SAT, no solver imports)"
        ),
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "tiling_radius": _TILING_RADIUS,
        "per_term_timeout_s": cli_args.get("per_term_timeout_s"),
        "overall_status": "PASS" if all_pass else "FAIL_OR_TIMEOUT",
        "results": records,
    }
    json_path = os.path.join(research_dir, "verify_method1-results.json")
    save_versioned(summary, json_path)

    log_lines = [
        "verify_method1 run log -- truncated-square (4.8.8) shell witness verifier",
        "=" * 70,
        f"Method: {summary['method']}",
        f"Timestamp: {summary['timestamp']}",
        f"Tiling radius: {_TILING_RADIUS}",
        f"Per-term timeout: {cli_args.get('per_term_timeout_s')} s",
        f"Overall: {summary['overall_status']}",
        "",
    ]
    for r in records:
        log_lines.append(
            f"  [{r['status']}] {r['detail']}  [{r['elapsed']:.2f}s]"
        )
    log_lines.append("")
    log_lines.append(
        "Disjoint code path: pure-Python BFS + vertex-intersection "
        "adjacency. Solver path: ShellSolverFramework + Cython "
        "Redelmeier enumeration."
    )
    log_text = "\n".join(log_lines)
    log_path = os.path.join(research_dir, "verify_method1-run-log.txt")
    save_versioned(log_text, log_path)


class Method1Verifier(VerifierBase):
    name = "verify_method1 (truncated-square shell witness, pure-Python)"
    description = (
        "Independent geometric witness verifier for the truncated-square "
        "(4.8.8) shell minimisation problem. For each proved n, "
        "validates that the solver's reported (hole, shell) pair is "
        "size-correct, both connected, disjoint, and the hole's "
        "corona is contained in the shell. Disjoint from the solver "
        "(no SAT backend, no Cython enumeration, independent face "
        "adjacency)."
    )
    default_max_n = 5
    verify_tag = "1"
    default_per_term_timeout = float(VERIFIER_TIMEOUT_S)

    def __init__(self):
        if not os.path.exists(_RESULTS_PATH):
            raise FileNotFoundError(
                f"solver-results.json not found at {_RESULTS_PATH}; "
                f"run the solver first."
            )
        with open(_RESULTS_PATH, "r", encoding="utf-8") as f:
            self._solver_results = json.load(f)
        self._records = []

    @classmethod
    def select_ns(cls, args):
        if not os.path.exists(_RESULTS_PATH):
            return []
        with open(_RESULTS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        proved = sorted(
            int(k) for k, v in data.items()
            if v.get("status") == STATUS_PROVED
        )
        if args.n is not None:
            return [args.n] if args.n in proved else []
        return [n for n in proved if n <= args.max_n]

    def verify_n(self, n):
        rec = verify_witness(
            n, self._solver_results, deadline=self._per_term_deadline
        )
        self._records.append(rec)
        if rec["status"] == "PASS":
            return rec["shell_size"], rec["detail"]
        if rec["status"] == STATUS_TIMEOUT:
            return None, f"TIMEOUT: {rec['detail']}"
        return None, rec["detail"]

    def expected(self, n):
        key = str(n)
        res = self._solver_results.get(key)
        if not res:
            return None
        return res.get("value")

    def save_artifacts(self, summary, log_text):
        _write_outputs(
            self._records,
            _PROJECT_DIR,
            summary["all_ok"],
            cli_args={"per_term_timeout_s": summary["per_term_timeout_s"]},
        )


if __name__ == "__main__":
    sys.exit(Method1Verifier.run())
