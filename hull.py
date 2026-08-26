# SPDX-License-Identifier: GPL-3.0-or-later

"""Convex hull: points in, local mesh out. StanHull and bmesh are adapters."""

import bmesh

from . import stanhull
from .constants import MIN_SIZE


def _valid_unique(elements, kind):
    seen = set()
    unique = []
    for elem in elements:
        if not isinstance(elem, kind) or not elem.is_valid or elem in seen:
            continue
        seen.add(elem)
        unique.append(elem)
    return unique


def _adapter_stanhull(unique_points, max_verts):
    hull = stanhull.build_hull(unique_points, max_verts)
    if hull is None:
        return None

    verts, tris = hull
    bm = bmesh.new()
    bm_verts = [bm.verts.new(co) for co in verts]
    for a, b, c in tris:
        if a == b or b == c or a == c:
            continue
        try:
            bm.faces.new((bm_verts[a], bm_verts[b], bm_verts[c]))
        except ValueError:
            continue
    bm.verts.ensure_lookup_table()
    return bm


def _adapter_exact(unique_points):
    bm = bmesh.new()
    for co in unique_points:
        bm.verts.new(co)
    bm.verts.ensure_lookup_table()

    verts = _valid_unique(bm.verts, bmesh.types.BMVert)
    result = bmesh.ops.convex_hull(bm, input=verts, use_existing_faces=False)

    keep = set()
    for elem in result.get("geom", []):
        if not getattr(elem, "is_valid", False):
            continue
        if isinstance(elem, bmesh.types.BMVert):
            keep.add(elem)
        elif isinstance(elem, bmesh.types.BMEdge):
            keep.update(v for v in elem.verts if v.is_valid)
        elif isinstance(elem, bmesh.types.BMFace):
            keep.update(v for v in elem.verts if v.is_valid)

    leftover = _valid_unique(
        (vert for vert in bm.verts if vert not in keep),
        bmesh.types.BMVert,
    )
    if leftover:
        bmesh.ops.delete(bm, geom=leftover, context="VERTS")
    return bm


def _reject_flat(bm):
    faces = _valid_unique(bm.faces, bmesh.types.BMFace)
    if not faces:
        bm.free()
        raise RuntimeError("Selection is flat or collinear; convex hull has no volume")

    bmesh.ops.recalc_face_normals(bm, faces=faces)

    area = sum(face.calc_area() for face in faces)
    diagonal = max((vert.co.length for vert in bm.verts), default=0.0)
    thickness = bm.calc_volume(signed=False) / max(area, 1e-12)
    if thickness < max(diagonal, MIN_SIZE) * 1e-5:
        bm.free()
        raise RuntimeError("Selection is flat or collinear; convex hull has no volume")
    return faces


def _inflate(bm, skin_width):
    if skin_width <= 0.0:
        return
    bm.normal_update()
    offsets = [
        vert.normal * skin_width * min(vert.calc_shell_factor(), 4.0)
        for vert in bm.verts
    ]
    for vert, offset in zip(bm.verts, offsets):
        vert.co += offset


def build(unique_points, max_verts=0, skin_width=0.0):
    """Local-space hull bmesh. Caller owns the mesh (to_mesh / free)."""
    bm = _adapter_stanhull(unique_points, max_verts)
    if bm is None:
        bm = _adapter_exact(unique_points)

    faces = _reject_flat(bm)
    _inflate(bm, skin_width)
    return bm, faces


def compute(unique_points, max_verts=0, skin_width=0.0):
    """Test surface: (verts xyz, face index loops). Frees the working mesh."""
    bm, _faces = build(unique_points, max_verts, skin_width)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    verts = [tuple(vert.co) for vert in bm.verts]
    faces = [tuple(vert.index for vert in face.verts) for face in bm.faces]
    bm.free()
    return verts, faces
