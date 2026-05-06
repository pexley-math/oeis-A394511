"""Manim animation of the truncated-square (4.8.8) shell for A394511.

Single continuous slide: the surrounding 4.8.8 tiling is drawn once,
sized so every solution n=1..20 fits, and then for each n the cells
flip color in place to show the current hole H (red) and the current
minimum enclosing shell C(H) (teal). No redraws between n -- just
color transitions on the same fixed cell objects.

The 4.8.8 geometry is built locally via sat_utils.tilings.truncsq;
vertex positions are derived from the (v, p, q) vertex labels using
the fundamental-domain offsets documented in that module.

Run:
    manim -qm generate-animation.py TruncSqShellExplainer
"""

import json
import math
import os
import sys

import numpy as np
from manim import (
    Scene, Polygon, VGroup, Text, FadeIn, FadeOut, Write,
    ORIGIN, UP, DOWN, BOLD,
    WHITE, GREY, GREY_B, GREY_D, YELLOW, RED, TEAL_C,
)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from sat_utils.tilings.truncsq import build_tiling


T = 1.0 / math.sqrt(2)
L = 1.0 + math.sqrt(2)


def vertex_xy(vlabel):
    v, p, q = vlabel
    base_x = p * L
    base_y = q * L
    if v == 1:
        return (base_x + T, base_y)
    if v == 2:
        return (base_x + L - T, base_y)
    if v == 3:
        return (base_x, base_y + T)
    if v == 4:
        return (base_x, base_y + L - T)
    raise ValueError(f"unknown vertex label v={v}")


def cell_polygon_xy(cell_info):
    pts = [vertex_xy(v) for v in cell_info['vertices']]
    cx = sum(x for x, _ in pts) / len(pts)
    cy = sum(y for _, y in pts) / len(pts)
    pts.sort(key=lambda p: math.atan2(p[1] - cy, p[0] - cx))
    return pts, (cx, cy)


HOLE_COLOR = RED
SHELL_COLOR = TEAL_C
EMPTY_FILL = GREY
EMPTY_OPACITY = 0.0
HOLE_OPACITY = 0.9
SHELL_OPACITY = 0.85
BG_STROKE = GREY_D
TARGET_HALF_WIDTH = 5.5
TARGET_HALF_HEIGHT = 2.6
BG_PAD = 1.2
TRANSITION_TIME = 0.6
HOLD_TIME = 1.5


class TruncSqShellExplainer(Scene):
    """A394511 a(1..20): hole + minimum enclosing shell on 4.8.8."""

    def construct(self):
        title = Text("A394511 -- Truncated-square shell",
                     font_size=40, weight=BOLD)
        sub = Text("Smallest connected shell enclosing an n-cell hole "
                   "on the 4.8.8 tiling",
                   font_size=22, color=GREY_B, weight=BOLD)
        sub.next_to(title, DOWN, buff=0.3)
        self.play(Write(title), FadeIn(sub))
        self.wait(1.6)
        self.play(FadeOut(title), FadeOut(sub))

        results_path = os.path.join(
            os.path.dirname(__file__), "..", "research",
            "solver-results.json",
        )
        with open(results_path, encoding="utf-8") as f:
            results = json.load(f)

        _v, _e, _adj, cells, _cell_adj = build_tiling(radius=8)
        cell_geom = {cid: cell_polygon_xy(info)
                     for cid, info in cells.items()}

        focus_cells = set()
        for n in range(1, 21):
            rec = results[str(n)]
            for c in rec["hole_cells"]:
                focus_cells.add(int(c))
            for c in rec["shell_cells"]:
                focus_cells.add(int(c))

        focus_pts = []
        for cid in focus_cells:
            pts, _ = cell_geom[cid]
            focus_pts.extend(pts)
        xs = [x for x, _ in focus_pts]
        ys = [y for _, y in focus_pts]
        fcx = (min(xs) + max(xs)) / 2
        fcy = (min(ys) + max(ys)) / 2
        half_w = (max(xs) - min(xs)) / 2 + 0.3
        half_h = (max(ys) - min(ys)) / 2 + 0.3

        s = min(TARGET_HALF_WIDTH / half_w, TARGET_HALF_HEIGHT / half_h)

        bg_half_w = half_w + BG_PAD
        bg_half_h = half_h + BG_PAD

        cell_polys = {}
        for cid, (pts, (cx, cy)) in cell_geom.items():
            if (abs(cx - fcx) > bg_half_w) or (abs(cy - fcy) > bg_half_h):
                continue
            arr = [np.array([(x - fcx) * s, (y - fcy) * s, 0])
                   for x, y in pts]
            poly = Polygon(*arr,
                           fill_color=EMPTY_FILL, fill_opacity=EMPTY_OPACITY,
                           stroke_color=BG_STROKE, stroke_width=1.0)
            cell_polys[cid] = poly

        all_group = VGroup(*cell_polys.values())
        self.play(FadeIn(all_group), run_time=1.0)
        self.wait(0.5)

        header = Text("a(1) = 4", font_size=44, color=YELLOW, weight=BOLD)
        header.to_edge(UP, buff=0.4)
        legend = Text("Hole H (red)   |   Shell C(H) (teal)",
                      font_size=22, color=GREY_B, weight=BOLD)
        legend.move_to([0, -3.4, 0])
        self.play(Write(header), FadeIn(legend))

        prev_hole = set()
        prev_shell = set()

        for n in range(1, 21):
            rec = results[str(n)]
            a_n = rec["value"]
            hole = {int(c) for c in rec["hole_cells"]}
            shell = {int(c) for c in rec["shell_cells"]}

            anims = []
            changed = (prev_hole | prev_shell | hole | shell)
            for cid in changed:
                if cid not in cell_polys:
                    continue
                poly = cell_polys[cid]
                if cid in hole:
                    anims.append(poly.animate.set_fill(
                        HOLE_COLOR, opacity=HOLE_OPACITY,
                    ).set_stroke(WHITE, width=2.0))
                elif cid in shell:
                    anims.append(poly.animate.set_fill(
                        SHELL_COLOR, opacity=SHELL_OPACITY,
                    ).set_stroke(WHITE, width=2.0))
                else:
                    anims.append(poly.animate.set_fill(
                        EMPTY_FILL, opacity=EMPTY_OPACITY,
                    ).set_stroke(BG_STROKE, width=1.0))

            new_header = Text(f"a({n}) = {a_n}",
                              font_size=44, color=YELLOW, weight=BOLD)
            new_header.to_edge(UP, buff=0.4)

            if n == 1:
                self.play(*anims, run_time=TRANSITION_TIME)
            else:
                self.play(*anims,
                          header.animate.become(new_header),
                          run_time=TRANSITION_TIME)
            self.wait(HOLD_TIME)

            prev_hole = hole
            prev_shell = shell

        self.wait(1.0)

        self.play(FadeOut(header), FadeOut(legend),
                  FadeOut(all_group), run_time=0.6)

        f1 = Text("a(n) = |corona(H)|  on the 4.8.8 tiling",
                  font_size=30, weight=BOLD)
        f2 = Text("a(1..20) = 4, 8, 8, 8, 8, 10, 10, 10, 12, 12,",
                  font_size=26, color=YELLOW, weight=BOLD)
        f3 = Text("12, 12, 12, 14, 14, 14, 14, 14, 16, 16",
                  font_size=26, color=YELLOW, weight=BOLD)
        fg = VGroup(f1, f2, f3).arrange(DOWN, buff=0.4).move_to(ORIGIN)
        self.play(Write(f1))
        self.wait(0.6)
        self.play(Write(f2), Write(f3))
        self.wait(3)
        self.play(FadeOut(fg))
