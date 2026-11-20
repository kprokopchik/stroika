"""3D-модель варианта из той же расстановки, что на чертеже, и рендер в Cycles.

Запуск (Python 3.11 с модулем bpy, см. README):
  python tools/scene3d.py --project projects/kvartira-95 --variant 1 --views all --out tmp/renders --samples 48
  python tools/scene3d.py --project projects/kvartira-95 --variant 1 --export projects/kvartira-95/models/v1.glb
Координаты плана в см: x вправо, y вниз. В Blender: X = x, Y = -y, Z вверх (метры).
"""
import argparse
import math
import os
import random
import sys

import bpy
import bmesh
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _project_dir():
    if "--project" in sys.argv:
        return os.path.abspath(sys.argv[sys.argv.index("--project") + 1])
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "projects", "kvartira-95"))


sys.path.insert(0, _project_dir())
from layout import VARIANTS  # noqa: E402
import scene_cfg as CFG  # noqa: E402

S = 0.01
ZOFF = 0         # подъём для кровати-чердака
EXPORT = False   # упрощённые материалы и без фасок для glTF
H = 270          # потолок
SILL = 55        # низ окна
HEAD = 250       # верх окна
DOOR_H = 210
rnd = random.Random(7)


# ------------------------------------------------------------------ материалы
MATS = {}


def principled(name, color, rough=0.5, metal=0.0, coat=0.0, sheen=0.0, emit=None, emit_s=0.0, transmission=0.0, alpha=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if coat:
        b.inputs["Coat Weight"].default_value = coat
    if sheen:
        b.inputs["Sheen Weight"].default_value = sheen
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = emit_s
    if transmission:
        b.inputs["Transmission Weight"].default_value = transmission
        b.inputs["IOR"].default_value = 1.45
    MATS[name] = m
    return m


def planks(name, c1, c2, w=1.2, hgt=0.19, mortar=(0.33, 0.24, 0.16), rough=0.42, rot=0.0):
    """Паркетная доска / плитка через Brick Texture в объектных координатах."""
    if EXPORT:
        return principled(name, tuple((a + b) / 2 for a, b in zip(c1, c2)), rough)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Rotation"].default_value = (0, 0, rot)
    br = nt.nodes.new("ShaderNodeTexBrick")
    br.inputs["Color1"].default_value = (*c1, 1)
    br.inputs["Color2"].default_value = (*c2, 1)
    br.inputs["Mortar"].default_value = (*mortar, 1)
    br.inputs["Scale"].default_value = 1.0
    br.inputs["Mortar Size"].default_value = 0.0025
    br.inputs["Brick Width"].default_value = w
    br.inputs["Row Height"].default_value = hgt
    br.offset = 0.37
    br.squash = 1.0
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 18.0
    nz.inputs["Detail"].default_value = 6.0
    mp2 = nt.nodes.new("ShaderNodeMapping")
    mp2.inputs["Scale"].default_value = (0.08, 2.5, 1) if rot == 0 else (2.5, 0.08, 1)
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 0.22
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.75, 0.75, 0.75, 1)
    ramp.color_ramp.elements[1].color = (1, 1, 1, 1)
    L = nt.links
    L.new(tc.outputs["Object"], mp.inputs["Vector"])
    L.new(mp.outputs["Vector"], br.inputs["Vector"])
    L.new(mp.outputs["Vector"], mp2.inputs["Vector"])
    L.new(mp2.outputs["Vector"], nz.inputs["Vector"])
    L.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    L.new(br.outputs["Color"], mix.inputs["A"])
    L.new(ramp.outputs["Color"], mix.inputs["B"])
    L.new(mix.outputs["Result"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough
    MATS[name] = m
    return m


def glass_mat(name):
    if EXPORT:
        m = principled(name, (0.80, 0.90, 0.95), 0.05)
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Alpha"].default_value = 0.25
        m.blend_method = "BLEND"
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    tr.inputs["Color"].default_value = (0.93, 0.97, 0.98, 1)
    gl = nt.nodes.new("ShaderNodeBsdfGlossy")
    gl.inputs["Roughness"].default_value = 0.02
    fr = nt.nodes.new("ShaderNodeFresnel")
    fr.inputs["IOR"].default_value = 1.5
    mix = nt.nodes.new("ShaderNodeMixShader")
    # отражение только с лицевой стороны, иначе полное внутреннее отражение даёт чёрные пятна
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    inv = nt.nodes.new("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    nt.links.new(geo.outputs["Backfacing"], inv.inputs[1])
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    nt.links.new(fr.outputs["Fac"], mul.inputs[0])
    nt.links.new(inv.outputs[0], mul.inputs[1])
    nt.links.new(mul.outputs[0], mix.inputs["Fac"])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(gl.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    m.blend_method = "BLEND" if hasattr(m, "blend_method") else None
    MATS[name] = m
    return m


def facade_mat(name, base, win):
    """Фасад соседних домов: стена с сеткой окон."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    br = nt.nodes.new("ShaderNodeTexBrick")
    br.inputs["Color1"].default_value = (*win, 1)
    br.inputs["Color2"].default_value = (win[0] * 0.8, win[1] * 0.85, win[2] * 0.9, 1)
    br.inputs["Mortar"].default_value = (*base, 1)
    br.inputs["Scale"].default_value = 1.0
    br.inputs["Mortar Size"].default_value = 1.15
    br.inputs["Brick Width"].default_value = 3.0
    br.inputs["Row Height"].default_value = 3.0
    br.offset = 0.0
    br.squash_frequency = 1
    nt.links.new(tc.outputs["Object"], br.inputs["Vector"])
    nt.links.new(br.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.6
    MATS[name] = m
    return m


def make_materials():
    principled("wall", (0.86, 0.85, 0.82), 0.92)
    principled("wallcap", (0.36, 0.44, 0.49), 0.8)
    principled("ceiling", (0.93, 0.93, 0.92), 0.95)
    planks("oak_floor", (0.62, 0.45, 0.29), (0.70, 0.52, 0.34))
    planks("tile_floor", (0.74, 0.72, 0.68), (0.76, 0.74, 0.70), w=0.6, hgt=0.6, mortar=(0.6, 0.59, 0.56), rough=0.35)
    planks("tile_wall", (0.90, 0.90, 0.88), (0.92, 0.92, 0.90), w=0.6, hgt=0.3, mortar=(0.72, 0.72, 0.70), rough=0.18)
    planks("tile_accent", (0.55, 0.62, 0.60), (0.57, 0.64, 0.62), w=0.6, hgt=0.3, mortar=(0.75, 0.76, 0.74), rough=0.2)
    principled("oak", (0.66, 0.49, 0.32), 0.45)
    principled("oak_dark", (0.42, 0.29, 0.18), 0.5)
    principled("white", (0.90, 0.90, 0.88), 0.35)
    principled("white_gloss", (0.92, 0.92, 0.91), 0.12, coat=0.3)
    principled("sage", (0.50, 0.58, 0.49), 0.45)
    principled("worktop", (0.90, 0.88, 0.84), 0.25)
    principled("backsplash", (0.80, 0.78, 0.73), 0.2)
    principled("fabric_green", (0.42, 0.52, 0.42), 0.95, sheen=0.4)
    principled("fabric_sand", (0.74, 0.68, 0.58), 0.95, sheen=0.4)
    principled("fabric_grey", (0.52, 0.53, 0.55), 0.95, sheen=0.4)
    principled("linen", (0.92, 0.91, 0.88), 0.9, sheen=0.3)
    principled("bed_blue", (0.56, 0.68, 0.84), 0.9, sheen=0.3)
    principled("bed_yellow", (0.92, 0.80, 0.52), 0.9, sheen=0.3)
    principled("bed_terra", (0.80, 0.55, 0.45), 0.9, sheen=0.3)
    principled("upholstery", (0.62, 0.60, 0.58), 0.95, sheen=0.3)
    principled("black", (0.02, 0.02, 0.022), 0.18)
    principled("steel", (0.75, 0.75, 0.77), 0.28, metal=1.0)
    principled("metal_dark", (0.08, 0.08, 0.08), 0.4, metal=0.6)
    principled("ceramic", (0.96, 0.96, 0.95), 0.08, coat=0.5)
    principled("mirror", (0.95, 0.95, 0.95), 0.02, metal=1.0)
    principled("rug_lilac", (0.78, 0.74, 0.86), 1.0)
    principled("rug_sand", (0.80, 0.76, 0.68), 1.0)
    principled("leaf", (0.12, 0.30, 0.10), 0.6)
    principled("pot", (0.82, 0.78, 0.72), 0.7)
    principled("lampshade", (0.98, 0.95, 0.88), 0.8, emit=(1.0, 0.82, 0.6), emit_s=2.5)
    principled("downlight", (1, 1, 1), 0.5, emit=(1.0, 0.9, 0.78), emit_s=6.0)
    principled("screen", (0.01, 0.012, 0.015), 0.08)
    principled("water", (0.85, 0.92, 0.95), 0.05)
    principled("ground", (0.38, 0.42, 0.34), 1.0)
    principled("asphalt", (0.30, 0.30, 0.31), 0.9)
    principled("tree", (0.20, 0.33, 0.16), 0.9)
    for i, c in enumerate([(0.55, 0.20, 0.18), (0.18, 0.32, 0.52), (0.85, 0.72, 0.35), (0.25, 0.45, 0.32), (0.9, 0.88, 0.82), (0.45, 0.30, 0.50), (0.85, 0.50, 0.30)]):
        principled(f"book{i}", c, 0.7)
    glass_mat("glass")
    facade_mat("facade1", (0.88, 0.85, 0.79), (0.42, 0.50, 0.56))
    facade_mat("facade2", (0.78, 0.68, 0.58), (0.40, 0.48, 0.54))


# ------------------------------------------------------------------ геометрия
COLL = None


def link(obj):
    COLL.objects.link(obj)
    return obj


def box(name, x1, y1, z1, x2, y2, z2, mat, bevel=0.0, seg=2, smooth=False):
    if x1 > x2:
        x1, x2 = x2, x1
    if y1 > y2:
        y1, y2 = y2, y1
    if z1 > z2:
        z1, z2 = z2, z1
    z1 += ZOFF
    z2 += ZOFF
    if EXPORT:
        bevel = 0
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    sx, sy, sz = (x2 - x1) * S, (y2 - y1) * S, (z2 - z1) * S
    cx, cy, cz = (x1 + x2) / 2 * S, -(y1 + y2) / 2 * S, (z1 + z2) / 2 * S
    for v in bm.verts:
        v.co.x = v.co.x * sx + cx
        v.co.y = v.co.y * sy + cy
        v.co.z = v.co.z * sz + cz
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.data.materials.append(MATS[mat])
    if bevel:
        md = ob.modifiers.new("bev", "BEVEL")
        md.width = bevel * S
        md.segments = seg
        md.limit_method = "NONE"
        md.harden_normals = not smooth
        if smooth:
            for p in me.polygons:
                p.use_smooth = True
    return link(ob)


def cyl(name, cx, cy, z1, z2, r, mat, verts=24, rx=None, ry=None):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=verts, radius1=1, radius2=1, depth=1)
    rx = rx if rx is not None else r
    ry = ry if ry is not None else r
    for v in bm.verts:
        v.co.x = v.co.x * rx * S + cx * S
        v.co.y = v.co.y * ry * S - cy * S
        v.co.z = (v.co.z + 0.5) * (z2 - z1) * S + z1 * S
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    ob.data.materials.append(MATS[mat])
    return link(ob)


def cone(name, cx, cy, z1, z2, r1, r2, mat, verts=32):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=False, segments=verts, radius1=r1 * S, radius2=r2 * S, depth=(z2 - z1) * S)
    for v in bm.verts:
        v.co.x += cx * S
        v.co.y += -cy * S
        v.co.z += (z1 + z2) / 2 * S
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    ob.data.materials.append(MATS[mat])
    return link(ob)


def sphere(name, cx, cy, cz, rx, ry, rz, mat):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=12, radius=1)
    for v in bm.verts:
        v.co.x = v.co.x * rx * S + cx * S
        v.co.y = v.co.y * ry * S - cy * S
        v.co.z = v.co.z * rz * S + cz * S
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    ob.data.materials.append(MATS[mat])
    return link(ob)


def rod(x1, y1, z1, x2, y2, z2, r, mat, verts=12):
    """Цилиндр между двумя точками (см)."""
    a = Vector((x1 * S, -y1 * S, (z1 + ZOFF) * S))
    b = Vector((x2 * S, -y2 * S, (z2 + ZOFF) * S))
    d = b - a
    me = bpy.data.meshes.new("rod")
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=verts, radius1=r * S, radius2=r * S, depth=d.length)
    q = Vector((0, 0, 1)).rotation_difference(d.normalized())
    for v in bm.verts:
        v.co = q @ v.co + (a + b) / 2
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new("rod", me)
    ob.data.materials.append(MATS[mat])
    return link(ob)


def disc_x(cx, cy, cz, r, th, mat):
    """Диск в плоскости YZ (колесо велосипеда, висящего перпендикулярно стене)."""
    me = bpy.data.meshes.new("disc")
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=28, radius1=1, radius2=1, depth=1)
    for v in bm.verts:
        v.co = Vector((v.co.z * th * S + cx * S, v.co.y * r * S - cy * S, v.co.x * r * S + (cz + ZOFF) * S))
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("disc", me)
    ob.data.materials.append(MATS[mat])
    return link(ob)


def area_light(name, x, y, z, sx, sy, power, color=(1.0, 0.86, 0.72), portal=False, rot=(0, 0, 0)):
    ld = bpy.data.lights.new(name, "AREA")
    ld.shape = "RECTANGLE"
    ld.size = sx * S
    ld.size_y = sy * S
    ld.energy = power
    ld.color = color
    if portal:
        ld.cycles.is_portal = True
    ob = bpy.data.objects.new(name, ld)
    ob.location = (x * S, -y * S, z * S)
    ob.rotation_euler = rot
    return link(ob)


# ------------------------------------------------------------------ анализ плана
class Model:
    def __init__(self, items):
        self.items = items
        self.walls = [i for i in items if i["kind"] == "wall"]
        self.windows = [i for i in items if i["kind"] == "window"]
        self.shafts = [i for i in items if i["kind"] == "shaft"]

    def solid_at(self, x, y):
        for w in self.walls + self.windows + self.shafts:
            if w["x1"] - 0.5 <= x <= w["x2"] + 0.5 and w["y1"] - 0.5 <= y <= w["y2"] + 0.5:
                return True
        return False

    def back(self, x, y, w, h):
        """Сторона предмета, прижатая к стене."""
        cand = []
        for side, px, py, ln in (("top", x + w / 2, y - 3, w), ("bottom", x + w / 2, y + h + 3, w),
                                 ("left", x - 3, y + h / 2, h), ("right", x + w + 3, y + h / 2, h)):
            hits = sum(self.solid_at(px + t * ln * 0.35 * (side in ("top", "bottom")), py + t * ln * 0.35 * (side in ("left", "right"))) for t in (-1, 0, 1))
            if hits:
                cand.append((hits, ln, side))
        if not cand:
            return "top"
        cand.sort(reverse=True)
        return cand[0][2]


def front_of(back):
    return {"top": "bottom", "bottom": "top", "left": "right", "right": "left"}[back]


def split_fronts(x, y, w, h, front, z1, z2, mat, panel=55, gap=0.5, depth=1.8, handle=True, handle_mat="metal_dark"):
    """Фасады шкафа: ряд дверей на передней стороне."""
    if front in ("top", "bottom"):
        n = max(1, round(w / panel))
        pw = w / n
        fy = y if front == "top" else y + h
        sgn = -1 if front == "top" else 1
        for i in range(n):
            a = x + i * pw + gap
            b = x + (i + 1) * pw - gap
            box("front", a, fy, z1 + gap, b, fy + sgn * depth, z2 - gap, mat, bevel=0.3, seg=1)
            if handle:
                hx = b - 4 if i % 2 == 0 else a + 4
                box("handle", hx - 0.6, fy + sgn * depth, (z1 + z2) / 2 - 15 if z2 - z1 > 120 else z2 - 12,
                    hx + 0.6, fy + sgn * (depth + 2), (z1 + z2) / 2 + 15 if z2 - z1 > 120 else z2 - 4, handle_mat)
    else:
        n = max(1, round(h / panel))
        ph = h / n
        fx = x if front == "left" else x + w
        sgn = -1 if front == "left" else 1
        for i in range(n):
            a = y + i * ph + gap
            b = y + (i + 1) * ph - gap
            box("front", fx, a, z1 + gap, fx + sgn * depth, b, z2 - gap, mat, bevel=0.3, seg=1)
            if handle:
                hy = b - 4 if i % 2 == 0 else a + 4
                box("handle", fx + sgn * depth, hy - 0.6, (z1 + z2) / 2 - 15 if z2 - z1 > 120 else z2 - 12,
                    fx + sgn * (depth + 2), hy + 0.6, (z1 + z2) / 2 + 15 if z2 - z1 > 120 else z2 - 4, handle_mat)


# ------------------------------------------------------------------ сборка
def merged_rects(rects):
    """Объединение прямоугольников стен без наложений: совпадающие грани дают чёрные полосы."""
    import numpy as np
    X0, Y0 = -40, -60
    g = np.zeros((1460, 960), dtype=bool)
    for x1, y1, x2, y2 in rects:
        g[int(round(y1)) - Y0:int(round(y2)) - Y0, int(round(x1)) - X0:int(round(x2)) - X0] = True
    out, open_runs = [], {}
    for r in range(g.shape[0] + 1):
        runs = set()
        if r < g.shape[0]:
            row = g[r]
            d = np.diff(np.concatenate(([0], row.astype(np.int8), [0])))
            runs = set(zip(np.where(d == 1)[0], np.where(d == -1)[0]))
        for run in list(open_runs):
            if run not in runs:
                out.append((run[0] + X0, open_runs.pop(run) + Y0, run[1] + X0, r + Y0))
        for run in runs:
            open_runs.setdefault(run, r)
    return out


def build_arch(m, cut=None, ceiling=True):
    top = cut if cut else H
    solid = [(w["x1"], w["y1"], w["x2"], w["y2"]) for w in m.walls + m.shafts]
    for x1, y1, x2, y2 in merged_rects(solid):
        box("wall", x1, y1, 0, x2, y2, top, "wall")
        if cut:
            box("cap", x1, y1, top, x2, y2, top + 0.6, "wallcap")
    # окна: подоконная часть, перемычка, рамы, стекло, подоконник
    for w in m.windows:
        x1, y1, x2, y2 = w["x1"], w["y1"], w["x2"], w["y2"]
        box("sill_wall", x1, y1, 0, x2, y2, SILL, "wall")
        if top > HEAD:
            box("lintel", x1, y1, HEAD, x2, y2, top, "wall")
        if cut:
            box("cap", x1, y1, min(top, HEAD) if top <= HEAD else top, x2, y2, (min(top, HEAD) if top <= HEAD else top) + 0.6, "wallcap")
        horiz = (x2 - x1) > (y2 - y1)
        zt = min(HEAD, top)
        if horiz:
            gy = (y1 + y2) / 2
            if not cut:
                box("glass", x1, gy - 0.4, SILL, x2, gy + 0.4, zt, "glass")
            box("frame", x1, gy - 3, SILL, x2, gy + 3, SILL + 5, "white")
            box("frame", x1, gy - 3, zt - 5, x2, gy + 3, zt, "white")
            n = max(1, round((x2 - x1) / 95))
            for i in range(n + 1):
                xx = x1 + (x2 - x1) * i / n
                box("frame", xx - 3, gy - 3, SILL, xx + 3, gy + 3, zt, "white")
            # подоконник со стороны комнаты (комната ниже по y)
            box("sill", x1, gy + 3, SILL - 3, x2, y2 + 6, SILL, "white")
        else:
            gx = (x1 + x2) / 2
            if not cut:
                box("glass", gx - 0.4, y1, SILL, gx + 0.4, y2, zt, "glass")
            box("frame", gx - 3, y1, SILL, gx + 3, y2, SILL + 5, "white")
            box("frame", gx - 3, y1, zt - 5, gx + 3, y2, zt, "white")
            n = max(1, round((y2 - y1) / 95))
            for i in range(n + 1):
                yy = y1 + (y2 - y1) * i / n
                box("frame", gx - 3, yy - 3, SILL, gx + 3, yy + 3, zt, "white")
            box("sill", x1 - 6, y1, SILL - 3, gx - 3, y2, SILL, "white")
    # двери: перемычки над проёмами и открытые полотна
    for d in [i for i in m.items if i["kind"] == "door"]:
        (hx, hy), (cx, cy), (ox, oy) = d["hinge"], d["closed"], d["opened"]
        if abs(hy - cy) < 0.1:      # проём вдоль x
            a, b = min(hx, cx), max(hx, cx)
            yy = [w for w in m.walls if w["y1"] - 1 <= hy <= w["y2"] + 1 and (abs(w["x2"] - a) < 2 or abs(w["x1"] - b) < 2)]
            t1, t2 = (yy[0]["y1"], yy[0]["y2"]) if yy else (hy - 5, hy + 5)
            if top > DOOR_H:
                box("lintel", a, t1, DOOR_H, b, t2, top, "wall")
            box("threshold", a, t1, -0.5, b, t2, 0.1, "oak_floor")
        else:
            a, b = min(hy, cy), max(hy, cy)
            xx = [w for w in m.walls if w["x1"] - 1 <= hx <= w["x2"] + 1 and (abs(w["y2"] - a) < 2 or abs(w["y1"] - b) < 2)]
            t1, t2 = (xx[0]["x1"], xx[0]["x2"]) if xx else (hx - 5, hx + 5)
            if top > DOOR_H:
                box("lintel", t1, a, DOOR_H, t2, b, top, "wall")
            box("threshold", t1, a, -0.5, t2, b, 0.1, "oak_floor")
        # полотно: открыто, или закрыто, если дверь в списке CLOSED
        if (hx, hy) in CLOSED:
            ox, oy = cx, cy
        if abs(ox - hx) > abs(oy - hy):
            box("door", min(hx, ox), hy - 2, 1, max(hx, ox), hy + 2, DOOR_H - 1, "white_gloss", bevel=0.4, seg=1)
        else:
            box("door", hx - 2, min(hy, oy), 1, hx + 2, max(hy, oy), DOOR_H - 1, "white_gloss", bevel=0.4, seg=1)
    # полы
    for f in [i for i in m.items if i["kind"] == "floor"]:
        me = bpy.data.meshes.new("floor")
        bm = bmesh.new()
        vs = [bm.verts.new((x * S, -y * S, 0)) for x, y in f["pts"]]
        try:
            face = bm.faces.new(vs)
        except ValueError:
            bm.free()
            continue
        bmesh.ops.recalc_face_normals(bm, faces=[face])
        if face.normal.z < 0:
            face.normal_flip()
        bm.to_mesh(me)
        bm.free()
        ob = bpy.data.objects.new("floor", me)
        ob.data.materials.append(MATS["tile_floor" if f["fk"] == "wet" else "oak_floor"])
        link(ob)
    if ceiling:
        box("ceiling", -30, -45, H, 900, 1385, H + 10, "ceiling")


def wet_panels(panels):
    """Плитка: (сторона стены, координата стены, от, до). top — стена сверху от комнаты и т. д."""
    t = 0.8
    for side, c, a, b in panels:
        if side == "top":
            box("tile", a, c, 0, b, c + t, 230, "tile_wall")
        elif side == "bottom":
            box("tile", a, c - t, 0, b, c, 230, "tile_wall")
        elif side == "left":
            box("tile", c, a, 0, c + t, b, 230, "tile_wall")
        else:
            box("tile", c - t, a, 0, c, b, 230, "tile_wall")




def wet_walls(m, rooms):
    """Плитка на стенах санузлов: тонкие панели вдоль стен, с пропуском дверей."""
    for (x1, y1, x2, y2, skips) in rooms:
        def seg(side, a, b):
            for s1, s2 in skips.get(side, []):
                if s1 > a:
                    yield a, s1
                a = max(a, s2)
            if b > a:
                yield a, b
        t = 0.8
        for a, b in seg("top", x1, x2):
            box("tile", a, y1, 0, b, y1 + t, 230, "tile_wall")
        for a, b in seg("bottom", x1, x2):
            box("tile", a, y2 - t, 0, b, y2, 230, "tile_wall")
        for a, b in seg("left", y1, y2):
            box("tile", x1, a, 0, x1 + t, b, 230, "tile_wall")
        for a, b in seg("right", y1, y2):
            box("tile", x2 - t, a, 0, x2, b, 230, "tile_wall")


def build_furniture(m, variant):
    items = m.items
    desks = [i for i in items if i["kind"] == "box" and i.get("k3") in ("desk", "dining")]
    kid_beds = ["bed_blue", "bed_yellow", "bed_terra"]
    kb = 0
    for it in items:
        k = it["kind"]
        if k == "wardrobe":
            x, y, w, h, fr = it["x"], it["y"], it["w"], it["h"], it["front"]
            # прихожая и коридор белые, спальни — светлый дуб
            mat = "white" if (y > 440 and x < 310) or x < 70 else ("oak" if y < 360 else "white")
            body = {"top": (x, y + 2, x + w, y + h), "bottom": (x, y, x + w, y + h - 2),
                    "left": (x + 2, y, x + w, y + h), "right": (x, y, x + w - 2, y + h)}[fr]
            box("wardrobe", body[0], body[1], 0, body[2], body[3], 250, mat)
            box("plinth", body[0], body[1], 0, body[2], body[3], 8, "white")
            split_fronts(*body[:2], body[2] - body[0], body[3] - body[1], fr, 8, 250, mat, panel=55)
        elif k == "shelf":
            x, y, w, h = it["x"], it["y"], it["w"], it["h"]
            bk = m.back(x, y, w, h)
            ht = 200 if (293 <= x <= 420 and y >= 810) else 190
            along = "x" if w >= h else "y"
            mat = "oak" if y > 360 else "white"
            # боковины и полки
            if along == "x":
                for xx in (x, x + w - 2):
                    box("side", xx, y, 0, xx + 2, y + h, ht, mat)
                n = 5
                for i in range(n + 1):
                    z = 6 + i * (ht - 8) / n
                    box("plank", x, y, z, x + w, y + h, z + 2, mat)
                box("back", x, y if bk == "top" else y + h - 1, 0, x + w, y + 1 if bk == "top" else y + h, ht, mat)
                for i in range(n):
                    z = 8 + i * (ht - 8) / n
                    xx = x + 4
                    while xx < x + w - 8:
                        bw = rnd.uniform(2.5, 4.5)
                        if rnd.random() < 0.82:
                            bh = rnd.uniform(18, min(30, (ht - 8) / n - 4))
                            d = h - 6
                            yy1 = y + 3 if bk == "top" else y + h - 3 - d
                            box("book", xx, yy1, z, xx + bw, yy1 + d, z + bh, f"book{rnd.randrange(7)}")
                        xx += bw + rnd.uniform(0, 1.2)
                        if rnd.random() < 0.06:
                            xx += rnd.uniform(10, 25)
            else:
                for yy in (y, y + h - 2):
                    box("side", x, yy, 0, x + w, yy + 2, ht, mat)
                n = 5
                for i in range(n + 1):
                    z = 6 + i * (ht - 8) / n
                    box("plank", x, y, z, x + w, y + h, z + 2, mat)
                for i in range(n):
                    z = 8 + i * (ht - 8) / n
                    yy = y + 4
                    while yy < y + h - 12:
                        bw = rnd.uniform(12, 30)
                        box("boxes", x + 3, yy, z, x + w - 4, yy + bw, z + rnd.uniform(14, 26), f"book{rnd.randrange(7)}" if rnd.random() < 0.3 else "fabric_sand", bevel=0.8)
                        yy += bw + rnd.uniform(2, 8)
        elif k == "bed":
            global ZOFF
            x, y, w, h, hd = it["x"], it["y"], it["w"], it["h"], it["head"]
            lift = it.get("lift") or 0
            if lift:
                build_loft_frame(m, x, y, w, h, lift)
                ZOFF = lift
            double = min(w, h) > 120
            bedmat = "linen" if double else kid_beds[kb % 3]
            if not double:
                kb += 1
            box("bedframe", x, y, 8, x + w, y + h, 32, "upholstery" if double else "oak", bevel=1.5, seg=2)
            for (lx, ly) in ((x + 4, y + 4), (x + w - 8, y + 4), (x + 4, y + h - 8), (x + w - 8, y + h - 8)):
                box("leg", lx, ly, 0, lx + 4, ly + 4, 8, "oak_dark")
            box("mattress", x + 2, y + 2, 32, x + w - 2, y + h - 2, 52, "linen", bevel=4, seg=3, smooth=True)
            if hd == "bottom":
                box("headboard", x - 2, y + h - 8, 8, x + w + 2, y + h, 115 if double else 90, "upholstery" if double else "oak", bevel=2.5, seg=3)
                pil = [(x + 8, y + h - 52, x + w / 2 - 4, y + h - 12)] if double else [(x + 10, y + h - 50, x + w - 10, y + h - 12)]
                if double:
                    pil.append((x + w / 2 + 4, y + h - 52, x + w - 8, y + h - 12))
                for p in pil:
                    box("pillow", p[0], p[1], 52, p[2], p[3], 66, "linen", bevel=5, seg=4, smooth=True)
                box("duvet", x - 1, y - 1, 50, x + w + 1, y + h - 58, 59, bedmat, bevel=4, seg=4, smooth=True)
                if double:
                    box("throw", x - 2, y - 2, 52, x + w + 2, y + 45, 61, "fabric_green", bevel=3, seg=3, smooth=True)
                    box("cushion", x + w / 2 - 22, y + h - 60, 58, x + w / 2 + 22, y + h - 46, 92, "fabric_sand", bevel=5, seg=4, smooth=True)
            elif hd == "top":
                box("headboard", x - 2, y, 8, x + w + 2, y + 8, 115 if double else 90, "upholstery" if double else "oak", bevel=2.5, seg=3)
                box("pillow", x + 10, y + 12, 52, x + w - 10, y + 50, 66, "linen", bevel=5, seg=4, smooth=True)
                box("duvet", x - 1, y + 58, 50, x + w + 1, y + h + 1, 59, bedmat, bevel=4, seg=4, smooth=True)
            elif hd == "left":
                box("headboard", x, y - 2, 8, x + 8, y + h + 2, 115 if double else 90, "upholstery" if double else "oak", bevel=2.5, seg=3)
                if double:
                    box("pillow", x + 12, y + 8, 52, x + 50, y + h / 2 - 4, 66, "linen", bevel=5, seg=4, smooth=True)
                    box("pillow", x + 12, y + h / 2 + 4, 52, x + 50, y + h - 8, 66, "linen", bevel=5, seg=4, smooth=True)
                else:
                    box("pillow", x + 12, y + 10, 52, x + 50, y + h - 10, 66, "linen", bevel=5, seg=4, smooth=True)
                box("duvet", x + 58, y - 1, 50, x + w + 1, y + h + 1, 59, bedmat, bevel=4, seg=4, smooth=True)
            elif hd == "right":
                box("headboard", x + w - 8, y - 2, 8, x + w, y + h + 2, 115 if double else 90, "upholstery" if double else "oak", bevel=2.5, seg=3)
                box("pillow", x + w - 50, y + 10, 52, x + w - 12, y + h - 10, 66, "linen", bevel=5, seg=4, smooth=True)
                box("duvet", x - 1, y - 1, 50, x + w - 58, y + h + 1, 59, bedmat, bevel=4, seg=4, smooth=True)
            ZOFF = 0
            if it.get("drawers"):
                fr = front_of(m.back(x, y, w, h))
                split_fronts(x + 10, y, w - 20, h, fr, 10, 30, "oak", panel=w / 2 - 12 if fr in ("top", "bottom") else h / 2, handle=False)
        elif k == "nightstand":
            x, y, w, h = it["x"], it["y"], it["w"], it["h"]
            box("nightstand", x + 1, y + 1, 0, x + w - 1, y + h - 1, 50, "oak", bevel=0.8, seg=1)
            cyl("lampbase", x + w / 2, y + h / 2, 50, 78, 4, "ceramic")
            cone("lampshade", x + w / 2, y + h / 2, 72, 92, 13, 10, "lampshade")
        elif k == "sofa":
            build_sofa(it["x"], it["y"], it["w"], it["h"], it["back"])
        elif k == "bench":
            x, y, w, h = it["x"], it["y"], it["w"], it["h"]
            box("benchbase", x, y, 0, x + w, y + h, 40, "white")
            split_fronts(x, y, w, h, "bottom", 4, 38, "white", panel=52, handle=False)
            box("benchseat", x + 1, y + 1, 40, x + w - 1, y + h + 2, 47, "fabric_sand", bevel=2.5, seg=3, smooth=True)
            box("benchback", x + 2, y, 47, x + w - 2, y + 12, 90, "fabric_sand", bevel=3, seg=3, smooth=True)
        elif k == "chair":
            if it.get("guest"):
                continue
            cx, cy, f, sz = it["cx"], it["cy"], it["facing"], 42
            x, y = cx - sz / 2, cy - sz / 2
            for (lx, ly) in ((x + 2, y + 2), (x + sz - 5, y + 2), (x + 2, y + sz - 5), (x + sz - 5, y + sz - 5)):
                box("leg", lx, ly, 0, lx + 3, ly + 3, 44, "oak")
            box("seat", x, y, 44, x + sz, y + sz, 48, "oak", bevel=0.8, seg=1)
            box("seatpad", x + 2, y + 2, 48, x + sz - 2, y + sz - 2, 51, "fabric_sand", bevel=1.2, seg=2)
            bkside = {"up": "bottom", "down": "top", "left": "right", "right": "left"}[f]
            if bkside == "bottom":
                box("back", x + 2, y + sz - 4, 51, x + sz - 2, y + sz - 1, 86, "oak", bevel=0.8, seg=1)
            elif bkside == "top":
                box("back", x + 2, y + 1, 51, x + sz - 2, y + 4, 86, "oak", bevel=0.8, seg=1)
            elif bkside == "right":
                box("back", x + sz - 4, y + 2, 51, x + sz - 1, y + sz - 2, 86, "oak", bevel=0.8, seg=1)
            else:
                box("back", x + 1, y + 2, 51, x + 4, y + sz - 2, 86, "oak", bevel=0.8, seg=1)
        elif k == "office_chair":
            cx, cy = it["cx"], it["cy"]
            # к ближайшему столу
            best = min(desks, key=lambda d: (d["x"] + d["w"] / 2 - cx) ** 2 + (d["y"] + d["h"] / 2 - cy) ** 2) if desks else None
            dx = (best["x"] + best["w"] / 2 - cx) if best else 1
            dy = (best["y"] + best["h"] / 2 - cy) if best else 0
            cyl("base", cx, cy, 2, 5, 26, "metal_dark", verts=5)
            cyl("stem", cx, cy, 5, 42, 2.5, "steel")
            box("seat", cx - 23, cy - 23, 42, cx + 23, cy + 23, 50, "fabric_grey", bevel=3, seg=3, smooth=True)
            if abs(dx) > abs(dy):
                bx = cx - 23 if dx > 0 else cx + 19
                box("back", bx, cy - 21, 54, bx + 4, cy + 21, 98, "fabric_grey", bevel=2, seg=3, smooth=True)
            else:
                by = cy - 23 if dy > 0 else cy + 19
                box("back", cx - 21, by, 54, cx + 21, by + 4, 98, "fabric_grey", bevel=2, seg=3, smooth=True)
        elif k == "stool":
            cyl("stool", it["cx"], it["cy"], 0, 65, it["r"] - 2, "oak")
        elif k == "box":
            x, y, w, h, cat, k3 = it["x"], it["y"], it["w"], it["h"], it["cat"], it.get("k3")
            if cat == "table" and k3 in ("desk", "dining"):
                top = 75
                tm = "oak" if k3 == "dining" else "white"
                box("tabletop", x, y, top - 3, x + w, y + h, top, tm, bevel=0.6, seg=1)
                lm = "metal_dark"
                for (lx, ly) in ((x + 3, y + 3), (x + w - 7, y + 3), (x + 3, y + h - 7), (x + w - 7, y + h - 7)):
                    box("leg", lx, ly, 0, lx + 4, ly + 4, top - 3, lm)
                if k3 == "desk":
                    # лампа и ноутбук
                    bk = m.back(x, y, w, h)
                    lx, ly = (x + w - 15, y + 12) if bk in ("top",) else ((x + w - 14, y + 14) if bk == "right" else (x + 14, y + 14))
                    cyl("desklamp", lx, ly, top, top + 42, 1.2, "metal_dark")
                    cone("deskshade", lx, ly, top + 34, top + 46, 8, 3, "lampshade")
                    cx2, cy2 = x + w / 2, y + h / 2
                    box("laptop", cx2 - 16, cy2 - 11, top, cx2 + 16, cy2 + 11, top + 1.5, "metal_dark")
                else:
                    cyl("vase", x + w / 2, y + h / 2, top, top + 22, 6, "ceramic")
                    sphere("flowers", x + w / 2, y + h / 2, top + 28, 10, 10, 8, "leaf")
            elif cat == "table":   # журнальный столик
                box("coffeetop", x, y, 38, x + w, y + h, 42, "oak", bevel=1.5, seg=2)
                for (lx, ly) in ((x + 4, y + 4), (x + w - 8, y + 4), (x + 4, y + h - 8), (x + w - 8, y + h - 8)):
                    box("leg", lx, ly, 0, lx + 4, ly + 4, 38, "oak_dark")
                box("rug", x - 60, y - 45, 0, x + w + 60, y + h + 45, 0.8, "rug_sand", bevel=0.3, seg=1)
            elif k3 == "commode":
                box("commode", x + 1, y + 1, 8, x + w - 1, y + h - 1, 85, "oak")
                box("plinth", x + 3, y + 3, 0, x + w - 3, y + h - 3, 8, "oak_dark")
                fr = front_of(m.back(x, y, w, h))
                for i in range(3):
                    z1 = 10 + i * 25
                    split_fronts(x + 1, y + 1, w - 2, h - 2, fr, z1, z1 + 24, "oak", panel=200, handle=False)
                cyl("vase", x + w * 0.3, y + h / 2, 85, 110, 5, "ceramic")
            elif k3 == "tvstand":
                box("tvstand", x + 1, y + 1, 12, x + w - 1, y + h - 1, 48, "oak")
                box("plinth", x + 4, y + 4, 0, x + w - 4, y + h - 4, 12, "metal_dark")
            elif k3 == "shoebench":
                box("shoebench", x, y, 0, x + w, y + h, 44, "white")
                split_fronts(x, y, w, h, front_of(m.back(x, y, w, h)), 2, 42, "white", panel=55, handle=False)
                box("cushion", x + 1, y + 1, 44, x + w - 1, y + h - 1, 50, "fabric_grey", bevel=2, seg=3, smooth=True)
                box("mirror", x + 10, y + 0.3, 110, x + w - 10, y + 1.1, 200, "mirror")
            elif k3 == "skis":
                cols = ["book0", "book1", "book2", "book3"]
                for i2 in range(4):
                    sx = x + 4 + i2 * 7
                    box("ski", sx, y + 6, 0, sx + 2.5, y + 14, 165 + i2 * 6, cols[i2], bevel=0.5, seg=1)
                    rod(sx + 1, y + 22, 0, sx + 1, y + 22, 120 + i2 * 5, 0.8, "metal_dark", verts=6)
            elif k3 == "sleds":
                box("sled", x + 2, y + 1, 110, x + 48, y + 6, 150, "book0", bevel=1, seg=2)
                for sx in (x + 56, x + 68):
                    rod(sx, y + 4, 40, sx, y + 4, 105, 1.4, "metal_dark", verts=8)
                    box("deck", sx - 6, y + 2, 30, sx + 6, y + 10, 40, "book1")
            elif k3 == "ladder":
                lift = 150
                for yy in (y + 3, y + h - 3):
                    box("rail", x + 6, yy - 2, 0, x + 12, yy + 2, lift + 70, "oak")
                for zz in range(25, lift + 40, 30):
                    box("rung", x + 6, y + 3, zz, x + 12, y + h - 3, zz + 3, "oak")
            elif k3 == "toybench":
                box("toybench", x, y, 0, x + w, y + h, 42, "white")
                split_fronts(x, y, w, h, front_of(m.back(x, y, w, h)), 4, 40, "white", panel=50, handle=False)
                box("cushion", x + 2, y + 1, 42, x + w - 2, y + h - 1, 48, "fabric_sand", bevel=2, seg=3, smooth=True)
                for i2, c in enumerate(("bed_blue", "bed_yellow", "bed_terra")):
                    box("pillow", x + 20 + i2 * 70, y + h - 14 if m.back(x, y, w, h) == "bottom" else y + 2, 48, x + 58 + i2 * 70, y + h - 2 if m.back(x, y, w, h) == "bottom" else y + 14, 82, c, bevel=4, seg=3, smooth=True)
            elif k3 == "ottoman":
                box("ottoman", x, y, 6, x + w, y + h, 46, "fabric_sand", bevel=3, seg=3, smooth=True)
                for (lx, ly) in ((x + 3, y + 3), (x + w - 7, y + 3), (x + 3, y + h - 7), (x + w - 7, y + h - 7)):
                    box("leg", lx, ly, 0, lx + 4, ly + 4, 6, "oak_dark")
            elif k3 == "tallcab":
                box("tallcab", x + 1, y + 1, 0, x + w - 1, y + h - 1, 200, "white_gloss")
                split_fronts(x + 1, y + 1, w - 2, h - 2, front_of(m.back(x, y, w, h)), 0, 200, "white_gloss", panel=30)
            elif k3 == "armchair":
                box("armchair", x, y, 6, x + w, y + h, 42, "fabric_sand", bevel=4, seg=3, smooth=True)
                box("armback", x + w - 16, y, 42, x + w, y + h, 85, "fabric_sand", bevel=5, seg=3, smooth=True)
            elif cat == "store":
                box("cabinet", x + 1, y + 1, 0, x + w - 1, y + h - 1, 85, "white")
            elif cat == "seat":
                box("seat", x, y, 0, x + w, y + h, 45, "fabric_sand", bevel=3, seg=3, smooth=True)
        elif k == "bike":
            build_bike(it["cx"], it["ywall"], it["length"], it["kid"])
        elif k == "slide":
            box("slidedoor", it["ox1"], it["oy1"], 1, it["ox2"], it["oy2"], 209, "white_gloss", bevel=0.4, seg=1)
            box("rail", it["x1"] - 1, it["y1"], 209, it["x2"] + 1, it["oy2"], 213, "metal_dark")
            box("lintel", it["x1"] - 10, it["y1"] + 2, 210, it["x1"] - 1, it["y2"] - 2, H, "wall")
            box("threshold", it["x1"] - 10, it["y1"] + 2, -0.5, it["x1"] - 1, it["y2"] - 2, 0.1, "oak_floor")
        elif k == "bridge":
            x, y, w, h = it["x"], it["y"], it["w"], it["h"]
            box("bridge", x, y, 192, x + w, y + h, 196, "oak")
            box("bridgeback", x, y, 196, x + w, y + 2, 228, "oak")
            for i2 in range(int(w // 9)):
                if rnd.random() < 0.7:
                    bx = x + 4 + i2 * 9
                    box("book", bx, y + 4, 196, bx + rnd.uniform(3, 6), y + h - 4, 196 + rnd.uniform(16, 24), f"book{rnd.randrange(7)}")
        elif k == "swedish":
            x, y, w, h = it["x"], it["y"], it["w"], it["h"]
            if h > w:
                rx = x + w / 2
                for yy in (y + 3, y + h - 3):
                    box("rail", rx - 2, yy - 3, 0, rx + 2, yy + 3, 240, "oak")
                for zz in range(18, 235, 24):
                    rod(rx, y + 3, zz, rx, y + h - 3, zz, 1.6, "oak", verts=8)
            else:
                ry = y + h / 2
                for xx in (x + 3, x + w - 3):
                    box("rail", xx - 3, ry - 2, 0, xx + 3, ry + 2, 240, "oak")
                for zz in range(18, 235, 24):
                    rod(x + 3, ry, zz, x + w - 3, ry, zz, 1.6, "oak", verts=8)
        elif k == "mat":
            x, y, w, h = it["x"], it["y"], it["w"], it["h"]
            box("mat", x, y, 0, x + w, y + h, 4, "bed_blue", bevel=1.5, seg=2)
        elif k == "rug":
            x, y, w, h = it["x"], it["y"], it["w"], it["h"]
            box("rug", x, y, 0, x + w, y + h, 1.0, "rug_lilac", bevel=0.4, seg=1)
            # игрушки: пуф и корзина
            sphere("pouf", x + w * 0.75, y + h * 0.35, 18, 20, 20, 18, "bed_yellow")
            cyl("basket", x + w * 0.2, y + h * 0.7, 1, 30, 16, "fabric_sand")
        elif k == "plant":
            cx, cy = it["cx"], it["cy"]
            cyl("pot", cx, cy, 0, 38, 14, "pot")
            for j in range(9):
                a = j * 2.39
                r = rnd.uniform(6, 14)
                sphere("leaves", cx + r * math.cos(a), cy + r * math.sin(a), rnd.uniform(60, 110), rnd.uniform(12, 18), rnd.uniform(12, 18), rnd.uniform(16, 26), "leaf")
            cyl("trunk", cx, cy, 38, 80, 1.5, "oak_dark")
        elif k == "tv" and it["h"] > it["w"]:
            x, y, w, h = it["x"], it["y"], it["w"], it["h"]
            cy = y + h / 2
            box("tv", x, cy - 61, 92, x + 3, cy + 61, 162, "black")
            box("screen", x + 3, cy - 60, 93, x + 3.2, cy + 60, 161, "screen")
        elif k == "tv":
            x, y, w, h = it["x"], it["y"], it["w"], it["h"]
            cx = x + w / 2
            big = y > 1000
            tw = 123 if big else 100
            th = 70 if big else 57
            z1 = 92 if big else 108
            box("tv", cx - tw / 2, y, z1, cx + tw / 2, y + 3, z1 + th, "black")
            box("screen", cx - tw / 2 + 1, y + (3.05 if not big else -0.05), z1 + 1, cx + tw / 2 - 1, y + (3.2 if not big else 0.05), z1 + th - 1, "screen")
        elif k == "counter":
            build_counter(m, it)
        elif k == "ksink":
            x, y, w, h = it["x"], it["y"], it["w"], it["h"]
            box("sinkbowl", x + 8, y + 8, 75, x + w - 8, y + h - 10, 90.4, "steel")
            fx = x + w / 2
            cyl("faucet", fx, y + h - 6, 90, 122, 1.4, "steel")
            box("spout", fx - 1.2, y + h - 22, 118, fx + 1.2, y + h - 6, 121, "steel")
        elif k == "cooktop":
            x, y, w, h = it["x"], it["y"], it["w"], it["h"]
            box("cooktop", x + 3, y + 4, 90, x + w - 3, y + h - 6, 90.8, "black")
        elif k == "appliance":
            build_appliance(m, it)
        elif k == "washer":
            x, y, w, h = it["x"], it["y"], it["w"], it["h"]
            bk = m.back(x, y, w, h)
            box("washer", x + 1, y + 1, 0, x + w - 1, y + h - 1, 85, "white_gloss", bevel=1.5, seg=2)
            fr = front_of(bk)
            if fr == "bottom":
                cylw(x + w / 2, y + h - 1, 42, 17)
            elif fr == "right":
                cylw_side(x + w - 1, y + h / 2, 42, 17)
        elif k == "bath":
            x, y, w, h = it["x"], it["y"], it["w"], it["h"]
            box("bath", x, y, 0, x + w, y + h, 58, "ceramic", bevel=2, seg=3)
            box("bathin", x + 7, y + 7, 18, x + w - 7, y + h - 7, 58.5, "water", bevel=6, seg=4, smooth=True)
            cyl("bathtap", x + 8, y + 8, 58, 72, 2, "steel")
            # штора/стеклянная шторка на половину ванны
            box("bathglass", x + w - 80, y + h - 1, 58, x + w - 2, y + h, 200, "glass")
        elif k == "walkin":
            x, y, w, h = it["x"], it["y"], it["w"], it["h"]
            gx1, gy1, gx2, gy2 = it["glass"]
            box("showerfloor", x, y, 0, x + w, y + h, 0.6, "tile_floor")
            box("glasspanel", min(gx1, gx2), gy1 - 0.5, 0.6, max(gx1, gx2), gy2 + 0.5, 205, "glass")
            box("glassprofile", min(gx1, gx2), gy1 - 1, 203, max(gx1, gx2), gy2 + 1, 205, "metal_dark")
            dx1, dy1, dx2, dy2 = it["drain"]
            box("drain", dx1 - 3, dy1, 0.6, dx2 + 3, dy2, 0.9, "steel")
            # лейка на стене слева
            if it.get("head", "bottom") == "top":
                hx = x + w / 2 + 15
                cyl("showerpipe", hx, y + 4, 100, 200, 1.2, "steel")
                cyl("showerhead", hx, y + 18, 198, 200, 12, "steel")
                box("arm", hx - 1, y + 2, 198, hx + 1, y + 18, 200, "steel")
                box("accent", x, y + 0.8, 0, x + w, y + 1.6, 230, "tile_accent")
            else:
                cyl("showerpipe", x + 35, y + h - 4, 100, 200, 1.2, "steel")
                cyl("showerhead", x + 35, y + h - 18, 198, 200, 12, "steel")
                box("arm", x + 34, y + h - 18, 198, x + 36, y + h - 2, 200, "steel")
                box("accent", x, y + h - 1.6, 0, x + w, y + h - 0.8, 230, "tile_accent")
        elif k == "wc":
            x, y, w, h, bkside = it["x"], it["y"], it["w"], it["h"], it["back"]
            cx = x + w / 2
            if bkside == "bottom":
                box("install", x - 15, y + h - 18, 0, x + w + 15, y + h, 115, "tile_wall")
                box("flush", cx - 11, y + h - 18.6, 95, cx + 11, y + h - 18, 110, "white_gloss")
                sphere("bowl", cx, y + (h - 18) / 2 + 3, 40, w / 2, (h - 18) / 2 + 4, 14, "ceramic")
                box("bowlback", cx - w / 2 + 3, y + h - 26, 30, cx + w / 2 - 3, y + h - 18, 48, "ceramic", bevel=3, seg=3, smooth=True)
        elif k == "basin":
            x, y, w, h, bkside = it["x"], it["y"], it["w"], it["h"], it["back"]
            box("vanity", x, y, 50, x + w, y + h, 84, "oak")
            box("basintop", x, y, 84, x + w, y + h, 88, "ceramic", bevel=1.5, seg=2)
            cx, cy = x + w / 2, y + h / 2
            if bkside == "left":
                box("mirror", x + 0.9, y + 4, 105, x + 1.7, y + h - 4, 185, "mirror")
                cyl("tap", x + 7, cy, 88, 104, 1.2, "steel")
            elif bkside == "right":
                box("mirror", x + w - 1.7, y + 4, 105, x + w - 0.9, y + h - 4, 185, "mirror")
                cyl("tap", x + w - 7, cy, 88, 104, 1.2, "steel")
            elif bkside == "bottom":
                box("mirror", x + 4, y + h - 1.7, 105, x + w - 4, y + h - 0.9, 185, "mirror")
                cyl("tap", cx, y + h - 7, 88, 104, 1.2, "steel")


def sofa_rect(x, y, w, h, back, u1, u2, v1, v2):
    """Локальные координаты дивана (u вдоль спинки, v от спинки) в прямоугольник плана."""
    if back == "top":
        return x + u1, y + v1, x + u2, y + v2
    if back == "bottom":
        return x + u1, y + h - v2, x + u2, y + h - v1
    if back == "left":
        return x + v1, y + u1, x + v2, y + u2
    return x + w - v2, y + u1, x + w - v1, y + u2


def build_sofa(x, y, w, h, back):
    L, D = (w, h) if back in ("top", "bottom") else (h, w)
    mat = "fabric_green"

    def part(name, u1, u2, v1, v2, z1, z2, m_=mat, bev=5, segs=4):
        rx1, ry1, rx2, ry2 = sofa_rect(x, y, w, h, back, u1, u2, v1, v2)
        box(name, rx1, ry1, z1, rx2, ry2, z2, m_, bevel=bev, seg=segs, smooth=True)

    part("sofabase", 0, L, 0, D, 6, 40, bev=3, segs=3)
    part("sofaback", 2, L - 2, 0, 22, 40, 82)
    part("arm", 0, 18, 0, D, 6, 62)
    part("arm", L - 18, L, 0, D, 6, 62)
    n = 3 if L > 190 else 2
    cw = (L - 36) / n
    for i in range(n):
        part("cushion", 18 + i * cw + 1, 18 + (i + 1) * cw - 1, 22, D - 2, 40, 50, bev=4)
        part("backcushion", 18 + i * cw + 2, 18 + (i + 1) * cw - 2, 20, 36, 50, 84, bev=6)
    part("throwpillow", 22, 64, 34, 46, 50, 88, m_="fabric_sand")
    part("throwpillow", L - 64, L - 22, 34, 46, 50, 88, m_="fabric_sand")
    for (u, v) in ((6, 6), (L - 10, 6), (6, D - 10), (L - 10, D - 10)):
        rx1, ry1, rx2, ry2 = sofa_rect(x, y, w, h, back, u, u + 4, v, v + 4)
        box("leg", rx1, ry1, 0, rx2, ry2, 6, "oak_dark")


def build_loft_frame(m, x, y, w, h, lift):
    """Стойки и бортик кровати-чердака."""
    for (px, py) in ((x, y), (x + w - 6, y), (x, y + h - 6), (x + w - 6, y + h - 6)):
        box("post", px, py, 0, px + 6, py + 6, lift + 70, "oak")
    bk = m.back(x, y, w, h)
    if bk in ("top", "bottom"):
        ry = y + h - 4 if bk == "top" else y
        box("rail", x + 30, ry, lift + 52, x + w - 6, ry + 4, lift + 72, "oak")
    else:
        rx = x + w - 4 if bk == "left" else x
        box("rail", rx, y + 30, lift + 52, rx + 4, y + h - 6, lift + 72, "oak")
    box("slats", x + 2, y + 2, lift + 4, x + w - 2, y + h - 2, lift + 8, "oak")


def build_bike(cx, ywall, length, kid):
    """Велосипед на крюке за переднее колесо, плоскость велосипеда перпендикулярна стене."""
    r = 24 if kid else 34
    hook = 175 if kid else 205
    if int(cx) % 2:
        hook -= 18
    fy = ywall - r - 4
    fz = hook - r
    wb = 72 if kid else 104
    rz = max(r + 2, fz - wb)
    ry = ywall - r - 14
    for (wy, wz) in ((fy, fz), (ry, rz)):
        disc_x(cx, wy, wz, r, 3, "black")
        disc_x(cx, wy, wz, r - 5, 3.6, "steel")
        disc_x(cx, wy, wz, 4, 5, "metal_dark")
    col = "book1" if not kid else ("book6" if int(cx) % 2 else "book3")
    rod(cx, fy, fz, cx, ywall - length + 10, (fz + rz) / 2 + 10, 2.0, col)
    rod(cx, ywall - length + 10, (fz + rz) / 2 + 10, cx, ry, rz, 2.0, col)
    rod(cx, fy, fz, cx, ry, rz, 1.8, col)
    hy = ywall - length + 18
    rod(cx - (20 if kid else 27), hy, fz - 12, cx + (20 if kid else 27), hy, fz - 12, 1.3, "metal_dark")
    box("saddle", cx - 6, ry - 26, rz + r - 4, cx + 6, ry - 6, rz + r + 2, "black", bevel=1, seg=2)
    rod(cx, ywall + 0.5, hook, cx, ywall - 8, hook + 2, 0.8, "steel", verts=6)


def cylw(cx, fy, cz, r):
    me = bpy.data.meshes.new("door")
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=32, radius1=r * S, radius2=r * S, depth=0.02)
    for v in bm.verts:
        v.co = Vector((v.co.x + cx * S, v.co.z - fy * S - 0.01, v.co.y + cz * S))
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("washdoor", me)
    ob.data.materials.append(MATS["metal_dark"])
    link(ob)


def cylw_side(fx, cy, cz, r):
    me = bpy.data.meshes.new("door")
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=32, radius1=r * S, radius2=r * S, depth=0.02)
    for v in bm.verts:
        v.co = Vector((v.co.z + fx * S + 0.01, v.co.x - cy * S, v.co.y + cz * S))
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("washdoor", me)
    ob.data.materials.append(MATS["metal_dark"])
    link(ob)


def build_counter(m, it):
    x, y, w, h = it["x"], it["y"], it["w"], it["h"]
    bk = m.back(x, y, w, h)
    fr = front_of(bk)
    # тумбы
    box("base", x, y, 10, x + w, y + h, 86, "sage")
    box("plinth", x + (3 if fr == "left" else 0), y + (3 if fr == "top" else 0), 0,
        x + w - (3 if fr == "right" else 0), y + h - (3 if fr == "bottom" else 0), 10, "metal_dark")
    box("worktop", x - (2 if fr == "left" else 0), y - (2 if fr == "top" else 0), 86,
        x + w + (2 if fr == "right" else 0), y + h + (2 if fr == "bottom" else 0), 90, "worktop")
    split_fronts(x, y, w, h, fr, 10, 86, "sage", panel=60, handle=True, handle_mat="steel")
    # фартук и верхние шкафы вдоль стены
    if bk == "bottom":
        box("splash", x, y + h - 1, 90, x + w, y + h, 145, "backsplash")
        upper(x, y + h - 35, x + w, y + h, "bottom")
    elif bk == "left":
        box("splash", x, y, 90, x + 1, y + h, 145, "backsplash")
        upper(x, y, x + 35, y + h, "left")


HOOD = []
CLOSED = set()


def upper(x1, y1, x2, y2, bk):
    """Верхние шкафы 145–220 см, над варочной — вытяжка."""
    segs = [(x1, x2)] if bk == "bottom" else [(y1, y2)]
    for hx1, hx2 in HOOD:
        if bk == "bottom" and x1 <= hx1 and hx2 <= x2:
            segs = [(x1, hx1), (hx2, x2)]
            box("hood", hx1, y1 + 5, 150, hx2, y2, 162, "steel")
            box("hoodbox", hx1, y1 + 5, 162, hx2, y2, 220, "white")
    for a, b in segs:
        if b - a < 5:
            continue
        if bk == "bottom":
            box("upper", a, y1, 145, b, y2, 220, "white")
            split_fronts(a, y1, b - a, y2 - y1, "top", 145, 220, "white", panel=50, handle=False)
        else:
            box("upper", x1, a, 145, x2, b, 220, "white")
            split_fronts(x1, a, x2 - x1, b - a, "right", 145, 220, "white", panel=50, handle=False)
        # подсветка под шкафами
    return


def build_appliance(m, it):
    x, y, w, h, k3 = it["x"], it["y"], it["w"], it["h"], it.get("k3")
    if k3 == "dw" or k3 is None:
        return
    bk = m.back(x, y, w, h)
    fr = front_of(bk)
    box("tall", x, y, 0, x + w, y + h, 220, "white")
    if k3 == "fridge":
        split_fronts(x, y, w, h, fr, 4, 85, "white", panel=200, handle=True, handle_mat="steel")
        split_fronts(x, y, w, h, fr, 86, 220, "white", panel=200, handle=True, handle_mat="steel")
    else:
        split_fronts(x, y, w, h, fr, 4, 76, "white", panel=200, handle=False)
        split_fronts(x, y, w, h, fr, 146, 220, "white", panel=200, handle=False)
        # духовка и СВЧ
        if fr == "right":
            box("oven", x + w, y + 3, 78, x + w + 1.5, y + h - 3, 136, "black")
            box("micro", x + w, y + 3, 138, x + w + 1.5, y + h - 3, 144 + 0, "metal_dark")
            box("micro", x + w, y + 3, 100 + 38, x + w + 1.5, y + h - 3, 176, "black")
        elif fr == "bottom":
            box("oven", x + 3, y + h, 78, x + w - 3, y + h + 1.5, 136, "black")
            box("micro", x + 3, y + h, 138, x + w - 3, y + h + 1.5, 176, "black")
        elif fr == "top":
            box("oven", x + 3, y - 1.5, 78, x + w - 3, y, 136, "black")
            box("micro", x + 3, y - 1.5, 138, x + w - 3, y, 176, "black")


def ceiling_lights(variant):
    """Точечные светильники и мягкие источники под потолком по комнатам."""
    rooms = CFG.light_rooms(variant)
    for name, (x1, y1, x2, y2) in rooms.items():
        w, h = x2 - x1, y2 - y1
        p = 0.9 * w * h / 1e4 * 4
        area_light(f"fill_{name}", (x1 + x2) / 2, (y1 + y2) / 2, H - 2, w * 0.6, h * 0.6, p, color=(1.0, 0.88, 0.76))
        # видимые точечные светильники
        nx = max(1, round(w / 170))
        ny = max(1, round(h / 170))
        for i in range(nx):
            for j in range(ny):
                cx = x1 + w * (i + 0.5) / nx
                cy = y1 + h * (j + 0.5) / ny
                cyl("spot", cx, cy, H - 0.6, H, 4.5, "downlight")
    # подвес над обеденным столом
    for it in VARIANT_ITEMS:
        if it["kind"] == "box" and it.get("k3") == "dining":
            cx, cy = it["x"] + it["w"] / 2, it["y"] + it["h"] / 2
            cyl("cord", cx, cy, 175, H, 0.3, "metal_dark")
            cone("pendant", cx, cy, 150, 178, 24, 3, "lampshade")


VARIANT_ITEMS = []


def exterior():
    # земля далеко внизу (этаж ~6) и соседние дома
    box("ground", -6000, -6000, -2200, 8000, 8000, -2190, "ground")
    box("road", 1300, -6000, -2189, 2000, 8000, -2188, "asphalt")
    box("road2", -6000, -1800, -2189, 8000, -1200, -2188, "asphalt")
    blocks = [
        (2600, -400, 3800, 1800, 3800, "facade1"),
        (2600, 2300, 3700, 3800, 2600, "facade2"),
        (-800, -3600, 1500, -2600, 3400, "facade2"),
        (1900, -3800, 3300, -2700, 2400, "facade1"),
        (-3200, -3400, -1500, -2400, 4200, "facade1"),
    ]
    for x1, y1, x2, y2, hgt, mt in blocks:
        box("building", x1, y1, -2190, x2, y2, hgt - 2190, mt)
    for i in range(14):
        tx = rnd.uniform(1050, 2400)
        ty = rnd.uniform(-1500, 2600)
        cyl("trunk", tx, ty, -2190, -1700, 12, "oak_dark")
        sphere("crown", tx, ty, -1550, rnd.uniform(160, 240), rnd.uniform(160, 240), rnd.uniform(200, 280), "tree")


def world(strength=1.0, elev=28, rot=-115, sun_e=3.2):
    w = bpy.data.worlds.new("sky")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes["Background"]
    sky = nt.nodes.new("ShaderNodeTexSky")
    sky.sky_type = "NISHITA"
    sky.sun_elevation = math.radians(elev)
    sky.sun_rotation = math.radians(rot)
    sky.sun_intensity = 0.6
    sky.sun_disc = False
    sky.altitude = 40
    nt.links.new(sky.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = strength
    sun = bpy.data.lights.new("sun", "SUN")
    sun.energy = sun_e
    sun.angle = math.radians(1.5)
    sun.color = (1.0, 0.93, 0.84)
    so = bpy.data.objects.new("sun", sun)
    # солнце светит с востока (справа на плане) и чуть с юга
    so.rotation_euler = (math.radians(90 - elev), 0, math.radians(rot + 180))
    link(so)


def portals(m):
    for w in m.windows:
        x1, y1, x2, y2 = w["x1"], w["y1"], w["x2"], w["y2"]
        zc = (SILL + HEAD) / 2
        if (x2 - x1) > (y2 - y1):
            # окно в верхней стене, комната ниже (y больше): свет внутрь по -Y blender → +y плана
            area_light("portal", (x1 + x2) / 2, y2 + 1, zc, x2 - x1, HEAD - SILL, 1, portal=True, rot=(math.radians(-90), 0, 0))
        else:
            area_light("portal", x1 - 1, (y1 + y2) / 2, zc, HEAD - SILL, y2 - y1, 1, portal=True, rot=(0, math.radians(90), 0))


def camera(name, pos, target, lens=16, ortho=None):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = 36
    cd.clip_start = 0.05
    cd.clip_end = 400
    if ortho:
        cd.type = "ORTHO"
        cd.ortho_scale = ortho
    ob = bpy.data.objects.new(name, cd)
    ob.location = (pos[0] * S, -pos[1] * S, pos[2] * S)
    d = Vector((target[0] * S, -target[1] * S, target[2] * S)) - ob.location
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    link(ob)
    return ob


VIEWS_BY_VARIANT = CFG.VIEWS_BY_VARIANT
VIEWS = VIEWS_BY_VARIANT[1]


def setup_render(samples, res, interior):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.02
    sc.cycles.use_denoising = True
    try:
        sc.cycles.denoiser = "OPENIMAGEDENOISE"
    except Exception:
        pass
    sc.cycles.max_bounces = 8
    sc.cycles.diffuse_bounces = 5
    sc.cycles.glossy_bounces = 3
    sc.cycles.transmission_bounces = 6
    sc.cycles.transparent_max_bounces = 12
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.cycles.sample_clamp_indirect = 8
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "JPEG"
    sc.render.image_settings.quality = 92
    sc.view_settings.view_transform = "AgX"
    try:
        sc.view_settings.look = "AgX - Medium High Contrast"
    except Exception:
        pass
    sc.view_settings.exposure = 0.0 if interior else -0.15


def build_scene(variant, interior, cut):
    global COLL, VARIANT_ITEMS
    bpy.ops.wm.read_factory_settings(use_empty=True)
    MATS.clear()
    HOOD.clear()
    COLL = bpy.context.scene.collection
    make_materials()
    p = VARIANTS[variant]()
    VARIANT_ITEMS[:] = p.items
    m = Model(p.items)
    for it in p.items:
        if it["kind"] == "cooktop":
            HOOD.append((it["x"], it["x"] + it["w"]))
    build_arch(m, cut=None if interior else cut, ceiling=interior)
    wet_panels(CFG.wet_panels(variant))
    build_furniture(m, variant)
    if interior:
        world(strength=0.9)
        exterior()
    else:
        world(strength=0.45, elev=55, rot=-140, sun_e=4.0)
        principled("studio", (0.70, 0.70, 0.68), 0.9)
        box("studio", -3000, -3000, -2, 4000, 4000, -1, "studio")
    if interior:
        portals(m)
        ceiling_lights(variant)
    return m


def export_glb(variant, cut, path):
    """Кукольный домик без потолка в .glb: материалы цветом, объекты слиты по материалам."""
    global EXPORT, COLL, VARIANT_ITEMS
    EXPORT = True
    bpy.ops.wm.read_factory_settings(use_empty=True)
    import addon_utils
    addon_utils.enable("io_scene_gltf2", default_set=True)
    MATS.clear()
    HOOD.clear()
    COLL = bpy.context.scene.collection
    make_materials()
    p = VARIANTS[variant]()
    VARIANT_ITEMS[:] = p.items
    m = Model(p.items)
    for it in p.items:
        if it["kind"] == "cooktop":
            HOOD.append((it["x"], it["x"] + it["w"]))
    build_arch(m, cut=cut, ceiling=False)
    wet_panels(CFG.wet_panels(variant))
    build_furniture(m, variant)
    # слить объекты по материалу и центрировать
    groups = {}
    for ob in list(bpy.data.objects):
        if ob.type != "MESH" or not ob.data.materials:
            continue
        groups.setdefault(ob.data.materials[0].name, []).append(ob)
    cx, cy = CFG.CENTER[0] * S, -CFG.CENTER[1] * S
    for mname, obs in groups.items():
        bm = bmesh.new()
        for ob in obs:
            me = ob.data
            tmp = bmesh.new()
            tmp.from_mesh(me)
            bmesh.ops.transform(tmp, matrix=ob.matrix_world, verts=tmp.verts)
            tmp.to_mesh(me)
            tmp.free()
            bm.from_mesh(me)
        for v in bm.verts:
            v.co.x -= cx
            v.co.y -= cy
        new = bpy.data.meshes.new(mname)
        bm.to_mesh(new)
        bm.free()
        new.materials.append(MATS[mname])
        for ob in obs:
            bpy.data.objects.remove(ob, do_unlink=True)
        link(bpy.data.objects.new(mname, new))
    bpy.ops.export_scene.gltf(filepath=os.path.abspath(path), export_format="GLB", export_apply=True,
                              export_lights=False, export_cameras=False, export_yup=True)
    print("EXPORTED", path, os.path.getsize(path) // 1024, "KB", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default="", help="папка объекта с layout.py и scene_cfg.py")
    ap.add_argument("--variant", type=int, default=1)
    ap.add_argument("--views", default="kitchen_from_hall")
    ap.add_argument("--out", default="3d")
    ap.add_argument("--samples", type=int, default=96)
    ap.add_argument("--res", default="1280x853")
    ap.add_argument("--cut", type=float, default=210)
    ap.add_argument("--blend", default="")
    ap.add_argument("--close", default="", help="петли закрытых дверей: x,y;x,y")
    ap.add_argument("--export", default="", help="путь .glb: модель-кукольный домик для веб-страницы")
    a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
    res = tuple(int(v) for v in a.res.split("x"))
    for pair in filter(None, a.close.split(";")):
        CLOSED.add(tuple(float(v) for v in pair.split(",")))
    if a.export:
        export_glb(a.variant, a.cut, a.export)
        return
    global VIEWS
    VIEWS = VIEWS_BY_VARIANT[a.variant]
    os.makedirs(a.out, exist_ok=True)
    views = list(VIEWS) if a.views == "all" else a.views.split(",")
    groups = {True: [v for v in views if VIEWS[v][3]], False: [v for v in views if not VIEWS[v][3]]}
    for interior, vs in groups.items():
        if not vs:
            continue
        build_scene(a.variant, interior, a.cut)
        setup_render(a.samples if interior else max(48, a.samples // 2), res, interior)
        if a.blend:
            bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.blend + ("_int" if interior else "_doll") + ".blend"))
        for v in vs:
            pos, tgt, lens, _ = VIEWS[v]
            cam = camera(v, pos, tgt, lens, ortho=CFG.TOP_ORTHO if v == "top" else None)
            bpy.context.scene.camera = cam
            if v == "top":
                bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y = (1000, 1300)
            else:
                bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y = res
            bpy.context.scene.render.filepath = os.path.abspath(os.path.join(a.out, f"v{a.variant}-{v}.jpg"))
            bpy.ops.render.render(write_still=True)
            print("RENDERED", v, flush=True)


if __name__ == "__main__":
    main()
