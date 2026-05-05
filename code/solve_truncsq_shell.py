"""
Minimum enclosing shell on the truncated square tiling (4.8.8).

a(n) = minimum number of cells in a connected shell that completely
encloses a connected region of n cells, where the complement
(exterior) is also connected.

Primary solver: Cython Redelmeier enumeration + bridge-gap shell
evaluation via ``sat_utils.tiling_enum.enumerate_and_eval``.

Key structural property (from session 4):
- Corona is ALWAYS connected (comps=1; vertex degree 3).
- Shell = |corona| exactly (zero bridges, zero extra).
- Therefore: a(n) = min over all n-cell connected polyforms H of
  |corona(H)|, which reduces to exhaustive enumeration + pick-min.

Phase 10a shared-lib migration (2026-04-10): the entire solve loop
now lives in ``sat_utils.frameworks.ShellSolverFramework`` with
``objective="enumeration"``. Pre-migration ``solve_truncsq_shell.py``
was 321 lines; the framework version is ~65 lines of glue.

No pre-primed values. All terms computed from scratch.

Usage:
    python solve_truncsq_shell.py --n 1-5
    python solve_truncsq_shell.py --n 1-13 --per-term-timeout 600
"""

import json
import os
import sys

from sat_utils.frameworks import ShellSolverFramework
from sat_utils.tilings.truncsq import build_tiling as _build_truncsq_tiling
from sat_utils.tiling_shell import build_vertex_to_cells, prepare_enum_data
from sat_utils.tiling_solver import find_center_cell as _find_center
from figure_gen_utils.solver_log import STATUS_PROVED


# Module-level state: per-cells-id cached enum data + cascading
# upper bound. Rebuilt once per build_tiling call.
_ENUM_STATE = {}
_PREV_SHELL = {"value": 0}

_RESULTS_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "research", "solver-results.json",
)


def _prev_shell_from_results(n):
    """Return max a(k) over PROVED k < n in solver-results.json, or 0."""
    path = os.path.abspath(_RESULTS_PATH)
    if not os.path.exists(path):
        return 0
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return 0
    best = 0
    for k_str, rec in data.items():
        try:
            k = int(k_str)
        except (TypeError, ValueError):
            continue
        if k >= n:
            continue
        if rec.get("status") != STATUS_PROVED:
            continue
        v = rec.get("value")
        if isinstance(v, int) and v > best:
            best = v
    return best


def _build_tiling_for_framework(radius):
    """Adapter: 4.8.8 5-tuple builder -> framework 3-tuple contract.

    Also initialises ``tiling_enum`` (Cython Redelmeier) once with
    the precomputed adjacency / cell-type / safe-cells / vnbr data.
    Caches the safe-cell iteration order keyed by ``id(cells)`` so
    ``enum_fn`` can reuse it.
    """
    import sat_utils.tiling_enum as tiling_enum

    _verts, _edges, _adj, cells, cell_adj = _build_truncsq_tiling(radius)
    v2c = build_vertex_to_cells(cells)
    adj_dict, cell_types, safe, full_degree, vnbr_dict, anchors = (
        prepare_enum_data(cells, cell_adj, v2c)
    )
    tiling_enum.init_tiling(
        adj_dict, cell_types, safe, full_degree, vnbr_dict, anchors,
    )
    _ENUM_STATE[id(cells)] = {"safe_sorted": sorted(safe)}

    center = _find_center(cells, cell_adj)
    if center is None:
        raise RuntimeError(
            "truncsq-shell: could not find center cell "
            "(radius too small?)")
    return cells, cell_adj, center


def _enum_fn(n, cells, cell_adj, upper_bound):
    """Redelmeier enumeration + bridge-gap evaluation for a(n).

    Adaptive cascading upper bound: tightens to ``a(n-1) + 4`` for the
    first transition (n<=2: a(2)-a(1)=4 is the only +4 jump) and to
    ``a(n-1) + 2`` for n>=3 (max observed delta in proved range is 2).
    The +2 bound was A/B-validated against +4 for n=1..17; both produce
    identical a(n). The tighter bound is ~3x faster at n=17 and extends
    the proved frontier.
    """
    import sat_utils.tiling_enum as tiling_enum
    del cell_adj  # handled inside tiling_enum via init_tiling

    state = _ENUM_STATE.get(id(cells))
    if state is None:
        raise RuntimeError(
            "truncsq-shell: tiling_enum not initialised for this "
            "cells instance -- call _build_tiling_for_framework first.")

    ub = upper_bound
    prev = _PREV_SHELL["value"]
    if prev == 0:
        # Subprocess-per-n callers (--per-term-timeout in solver_cli) reset
        # module state on every child. Recover the cascade by reading the
        # last proved a(n-1) from solver-results.json, if present.
        prev = _prev_shell_from_results(n)
    if prev > 0:
        delta = 4 if n <= 2 else 2
        ub = min(ub, prev + delta)

    # tiling_enum.enumerate_and_eval initialises g_min_shell = upper_bound
    # and updates strictly (`shell < g_min_shell`). When the actual a(n)
    # equals the cascade-tightened upper_bound, the strict-less check
    # never fires and best_poly is left uninitialised. Pass ub + 1 so
    # the strict-less check captures the case shell == ub correctly.
    count, min_shell, best_poly = tiling_enum.enumerate_and_eval(
        n, state["safe_sorted"], upper_bound=ub + 1,
    )
    if min_shell == ub + 1:
        # No polyform with shell <= ub exists; the cascade hypothesis was
        # too tight. Re-run unbounded (framework default upper_bound).
        count, min_shell, best_poly = tiling_enum.enumerate_and_eval(
            n, state["safe_sorted"], upper_bound=upper_bound,
        )

    if min_shell is not None:
        _PREV_SHELL["value"] = min_shell

    best_hole = list(best_poly) if best_poly else None
    return count, min_shell, best_hole


solver = ShellSolverFramework(
    seq_id="NEW",
    description=(
        "Minimum enclosing shell on truncated square tiling (4.8.8)"
    ),
    method_label=(
        "Redelmeier enumeration + bridge-gap shell (corona on 4.8.8)"
    ),
    software_label="solve_truncsq_shell.py via ShellSolverFramework",
    geometry="truncated_square",
    build_tiling=_build_tiling_for_framework,
    objective="enumeration",
    tiling_radius=8,
    enum_fn=_enum_fn,
)


if __name__ == "__main__":
    sys.exit(solver.main())
