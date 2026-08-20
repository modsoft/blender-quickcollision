# SPDX-License-Identifier: MIT

import bmesh
import bpy
import re
from math import cos, pi, sin, tau
from mathutils import Matrix

from . import stanhull
from .constants import COLOR, MAT_NAME, MIN_SIZE


def unique_object_name(base):
    if base not in bpy.data.objects:
        return base
    index = 1
    while True:
        candidate = f"{base}_{index:02d}"
        if candidate not in bpy.data.objects:
            return candidate
        index += 1


def collider_name(prefix, source_name, suffix):
    """UE-style numbering: a numeric suffix (_00) counts up from itself."""
    match = re.fullmatch(r"(.*?)(\d+)", suffix)
    if match is None:
        return unique_object_name(f"{prefix}{source_name}{suffix}")

    stem, digits = match.groups()
    index = int(digits)
    width = len(digits)
    while True:
        candidate = f"{prefix}{source_name}{stem}{index:0{width}d}"
        if candidate not in bpy.data.objects:
            return candidate
        index += 1


def _new_object(context, name, bm):
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    mesh.update()
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    context.scene.collection.objects.link(obj)
    return obj


def _collection_in_scene(root, col):
    if root == col:
        return True
    return any(_collection_in_scene(child, col) for child in root.children)


def ensure_collection(scene, name):
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        scene.collection.children.link(col)
    elif not _collection_in_scene(scene.collection, col):
        scene.collection.children.link(col)
    return col


def move_to_collection(obj, col):
    for existing in list(obj.users_collection):
        existing.objects.unlink(obj)
    if obj.name not in col.objects:
        col.objects.link(obj)


def parent_keep_world(child, parent):
    world = child.matrix_world.copy()
    child.parent = parent
    child.matrix_parent_inverse = parent.matrix_world.inverted_safe()
    child.matrix_world = world


def ensure_collider_material():
    mat = bpy.data.materials.get(MAT_NAME)
    if mat is None:
        mat = bpy.data.materials.new(MAT_NAME)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf is not None:
            bsdf.inputs["Base Color"].default_value = (*COLOR[:3], 1.0)
            if "Alpha" in bsdf.inputs:
                bsdf.inputs["Alpha"].default_value = COLOR[3]
        if hasattr(mat, "blend_method"):
            try:
                mat.blend_method = "BLEND"
            except TypeError:
                pass
        if hasattr(mat, "surface_render_method"):
            mat.surface_render_method = "BLENDED"
    mat.diffuse_color = COLOR
    return mat


def apply_collider_look(obj, wire=False):
    obj.color = COLOR
    mat = ensure_collider_material()
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)
    obj.display_type = "WIRE" if wire else "TEXTURED"


def select_only(context, obj):
    if context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    for selected in list(context.selected_objects):
        selected.select_set(False)
    obj.select_set(True)
    context.view_layer.objects.active = obj


def make_box(context, name, matrix, size):
    sx, sy, sz = (max(float(s), MIN_SIZE) for s in size)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    obj = _new_object(context, name, bm)
    obj.matrix_world = matrix
    return obj


def make_sphere(context, name, center, radius):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(
        bm,
        u_segments=16,
        v_segments=8,
        radius=max(radius, MIN_SIZE),
    )
    for face in bm.faces:
        face.smooth = True
    obj = _new_object(context, name, bm)
    obj.matrix_world = Matrix.Translation(center)
    return obj


def make_capsule(context, name, matrix, radius, cyl_length):
    radius = max(radius, MIN_SIZE * 0.5)
    cyl_length = max(cyl_length, 0.0)
    bm = bmesh.new()
    segments = 16
    hemisphere_rings = 4
    half = cyl_length * 0.5

    rings = [[bm.verts.new((0.0, 0.0, -half - radius))]]
    for index in range(1, hemisphere_rings):
        angle = -0.5 * pi + index * (0.5 * pi / hemisphere_rings)
        ring_radius = radius * cos(angle)
        z = -half + radius * sin(angle)
        rings.append(
            [
                bm.verts.new(
                    (
                        ring_radius * cos(tau * segment / segments),
                        ring_radius * sin(tau * segment / segments),
                        z,
                    )
                )
                for segment in range(segments)
            ]
        )

    def equator(z):
        return [
            bm.verts.new(
                (
                    radius * cos(tau * segment / segments),
                    radius * sin(tau * segment / segments),
                    z,
                )
            )
            for segment in range(segments)
        ]

    rings.append(equator(-half))
    if half > 1e-8:
        rings.append(equator(half))

    for index in range(1, hemisphere_rings):
        angle = index * (0.5 * pi / hemisphere_rings)
        ring_radius = radius * cos(angle)
        z = half + radius * sin(angle)
        rings.append(
            [
                bm.verts.new(
                    (
                        ring_radius * cos(tau * segment / segments),
                        ring_radius * sin(tau * segment / segments),
                        z,
                    )
                )
                for segment in range(segments)
            ]
        )
    rings.append([bm.verts.new((0.0, 0.0, half + radius))])

    for lower, upper in zip(rings, rings[1:]):
        if len(lower) == 1:
            for index in range(segments):
                bm.faces.new((lower[0], upper[(index + 1) % segments], upper[index]))
        elif len(upper) == 1:
            for index in range(segments):
                bm.faces.new((lower[index], lower[(index + 1) % segments], upper[0]))
        else:
            for index in range(segments):
                next_index = (index + 1) % segments
                bm.faces.new(
                    (
                        lower[index],
                        lower[next_index],
                        upper[next_index],
                        upper[index],
                    )
                )

    for face in bm.faces:
        face.smooth = True
    obj = _new_object(context, name, bm)
    obj.matrix_world = matrix
    return obj


def _valid_unique(elements, kind):
    seen = set()
    unique = []
    for elem in elements:
        if not isinstance(elem, kind) or not elem.is_valid or elem in seen:
            continue
        seen.add(elem)
        unique.append(elem)
    return unique


def _hull_bmesh_stanhull(unique_points, max_verts):
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
            # Duplicate face in the result; safe to skip.
            continue
    bm.verts.ensure_lookup_table()
    return bm


def _hull_bmesh_exact(unique_points):
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


def make_convex(context, name, points, max_verts=0, skin_width=0.0):
    from .geometry import aabb_center

    center = aabb_center(points)
    unique_points = []
    seen = set()
    for point in points:
        local = point - center
        key = (round(local.x, 6), round(local.y, 6), round(local.z, 6))
        if key in seen:
            continue
        seen.add(key)
        unique_points.append(local)

    if len(unique_points) < 4:
        raise RuntimeError("Convex hull needs at least 4 distinct points")

    bm = _hull_bmesh_stanhull(unique_points, max_verts)
    if bm is None:
        bm = _hull_bmesh_exact(unique_points)

    faces = _valid_unique(bm.faces, bmesh.types.BMFace)
    if not faces:
        bm.free()
        raise RuntimeError("Selection is flat or collinear; convex hull has no volume")

    bmesh.ops.recalc_face_normals(bm, faces=faces)

    # A coplanar selection still produces faces, just with no enclosed volume.
    area = sum(face.calc_area() for face in faces)
    diagonal = max((vert.co.length for vert in bm.verts), default=0.0)
    thickness = bm.calc_volume(signed=False) / max(area, 1e-12)
    if thickness < max(diagonal, MIN_SIZE) * 1e-5:
        bm.free()
        raise RuntimeError("Selection is flat or collinear; convex hull has no volume")

    if skin_width > 0.0:
        # StanHull's own skin flag extrudes new geometry and blows the vertex
        # budget, so inflate here instead: push verts along their normals with
        # shell-factor compensation so each face plane moves by ~skin_width.
        bm.normal_update()
        offsets = [
            vert.normal * skin_width * min(vert.calc_shell_factor(), 4.0)
            for vert in bm.verts
        ]
        for vert, offset in zip(bm.verts, offsets):
            vert.co += offset

    vert_count = len(bm.verts)
    tri_count = sum(max(len(face.verts) - 2, 0) for face in faces)
    obj = _new_object(context, name, bm)
    obj.matrix_world = Matrix.Translation(center)
    return obj, (vert_count, tri_count)
