# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
# ##### END GPL LICENSE BLOCK #####

import bmesh
import bpy
from math import cos, pi, sin, tau
from mathutils import Matrix

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


def apply_collider_look(obj):
    obj.color = COLOR
    mat = ensure_collider_material()
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)


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


def make_convex(context, name, points):
    from .geometry import aabb_center

    center = aabb_center(points)
    bm = bmesh.new()
    for point in points:
        bm.verts.new(point - center)
    bm.verts.ensure_lookup_table()
    result = bmesh.ops.convex_hull(bm, input=bm.verts, use_existing_faces=False)
    interior = [
        elem
        for elem in result.get("geom_interior", [])
        if isinstance(elem, bmesh.types.BMVert)
    ]
    unused = [
        elem
        for elem in result.get("geom_unused", [])
        if isinstance(elem, bmesh.types.BMVert)
    ]
    to_delete = interior + unused
    if to_delete:
        bmesh.ops.delete(bm, geom=to_delete, context="VERTS")

    tri_count = sum(max(len(face.verts) - 2, 0) for face in bm.faces)
    obj = _new_object(context, name, bm)
    obj.matrix_world = Matrix.Translation(center)
    return obj, tri_count
