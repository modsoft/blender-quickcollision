# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
# ##### END GPL LICENSE BLOCK #####

from math import atan2, cos, sin
from mathutils import Matrix, Vector

from .constants import MIN_SIZE

_WORLD_AXES = (
    Vector((1.0, 0.0, 0.0)),
    Vector((0.0, 1.0, 0.0)),
    Vector((0.0, 0.0, 1.0)),
)


def mesh_objects(context):
    if context.mode == "EDIT_MESH":
        return [obj for obj in context.objects_in_mode if obj.type == "MESH"]
    return [obj for obj in context.selected_objects if obj.type == "MESH"]


def source_object(context):
    obj = context.active_object
    if obj is not None and obj.type == "MESH":
        return obj
    meshes = mesh_objects(context)
    return meshes[0] if meshes else None


def gather_points(context):
    """World-space points from the current mesh selection."""
    points = []
    if context.mode == "EDIT_MESH":
        import bmesh

        for obj in mesh_objects(context):
            bm = bmesh.from_edit_mesh(obj.data)
            mw = obj.matrix_world
            used = set()

            def add(vert):
                idx = vert.index
                if idx not in used:
                    used.add(idx)
                    points.append(mw @ vert.co.copy())

            for face in bm.faces:
                if face.select:
                    for vert in face.verts:
                        add(vert)
            for edge in bm.edges:
                if edge.select:
                    for vert in edge.verts:
                        add(vert)
            for vert in bm.verts:
                if vert.select:
                    add(vert)
        return points

    depsgraph = context.evaluated_depsgraph_get()
    for obj in mesh_objects(context):
        eval_obj = obj.evaluated_get(depsgraph)
        mesh = eval_obj.to_mesh()
        try:
            mw = eval_obj.matrix_world
            points.extend(mw @ vert.co.copy() for vert in mesh.vertices)
        finally:
            eval_obj.to_mesh_clear()
    return points


def aabb_center(points):
    xs = [p.x for p in points]
    ys = [p.y for p in points]
    zs = [p.z for p in points]
    return Vector(
        (
            (min(xs) + max(xs)) * 0.5,
            (min(ys) + max(ys)) * 0.5,
            (min(zs) + max(zs)) * 0.5,
        )
    )


def furthest_distance(origin, points):
    return max((p - origin).length for p in points)


def _normalize_axes(axes):
    out = []
    for axis in axes:
        vec = Vector(axis)
        if vec.length_squared < 1e-12:
            return None
        out.append(vec.normalized())
    if out[0].cross(out[1]).dot(out[2]) < 0.0:
        out[2] = -out[2]
    return tuple(out)


def extents_along(points, center, axes):
    sizes = []
    offsets = []
    for axis in axes:
        dots = [(p - center).dot(axis) for p in points]
        dmin = min(dots)
        dmax = max(dots)
        sizes.append(dmax - dmin)
        offsets.append((dmax + dmin) * 0.5)
    pos = center.copy()
    for axis, offset in zip(axes, offsets):
        pos += axis * offset
    return pos, sizes


def matrix_from_axes(axes, origin):
    mat = Matrix.Identity(4)
    for i, axis in enumerate(axes):
        col = axis.to_4d()
        col.w = 0.0
        mat.col[i] = col
    loc = origin.to_4d()
    loc.w = 1.0
    mat.col[3] = loc
    return mat


def oriented_bounds(points, axes):
    axes = _normalize_axes(axes)
    if axes is None:
        axes = _WORLD_AXES
    center = aabb_center(points)
    origin, sizes = extents_along(points, center, axes)
    return matrix_from_axes(axes, origin), sizes


def world_axes():
    return _WORLD_AXES


def object_axes(obj):
    mw = obj.matrix_world
    axes = [mw.col[i].xyz.normalized() for i in range(3)]
    return _normalize_axes(axes) or _WORLD_AXES


def _symmetric_eigenvectors(matrix):
    """Return eigenvalue/vector pairs for a real symmetric 3x3 matrix."""
    values = [list(row) for row in matrix]
    vectors = [
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ]

    for _iteration in range(24):
        p, q = max(
            ((0, 1), (0, 2), (1, 2)),
            key=lambda pair: abs(values[pair[0]][pair[1]]),
        )
        if abs(values[p][q]) < 1e-12:
            break

        angle = 0.5 * atan2(
            2.0 * values[p][q],
            values[q][q] - values[p][p],
        )
        c = cos(angle)
        s = sin(angle)
        app = values[p][p]
        aqq = values[q][q]
        apq = values[p][q]

        for i in range(3):
            if i in (p, q):
                continue
            aip = values[i][p]
            aiq = values[i][q]
            values[i][p] = values[p][i] = c * aip - s * aiq
            values[i][q] = values[q][i] = s * aip + c * aiq

        values[p][p] = c * c * app - 2.0 * s * c * apq + s * s * aqq
        values[q][q] = s * s * app + 2.0 * s * c * apq + c * c * aqq
        values[p][q] = values[q][p] = 0.0

        for i in range(3):
            vip = vectors[i][p]
            viq = vectors[i][q]
            vectors[i][p] = c * vip - s * viq
            vectors[i][q] = s * vip + c * viq

    pairs = []
    for column in range(3):
        vector = Vector(vectors[row][column] for row in range(3)).normalized()
        pairs.append((values[column][column], vector))
    return sorted(pairs, key=lambda pair: pair[0], reverse=True)


def covariance_axes(points, single_axis=False):
    if len(points) < 3:
        return _WORLD_AXES

    mean = sum(points, Vector((0.0, 0.0, 0.0))) / len(points)
    cov = [[0.0] * 3 for _ in range(3)]
    for point in points:
        delta = point - mean
        for row in range(3):
            for column in range(row, 3):
                cov[row][column] += delta[row] * delta[column]
    scale = 1.0 / len(points)
    for row in range(3):
        for column in range(row, 3):
            cov[row][column] *= scale
            cov[column][row] = cov[row][column]

    pairs = _symmetric_eigenvectors(cov)
    evals = [pair[0] for pair in pairs]
    if abs(evals[0] - evals[2]) < 1e-8:
        return _WORLD_AXES

    primary = pairs[0][1]

    if single_axis or abs(evals[1] - evals[2]) < 1e-8:
        helper = Vector((0.0, 0.0, 1.0))
        secondary = helper.cross(primary)
        if secondary.length_squared < 1e-8:
            secondary = Vector((1.0, 0.0, 0.0)).cross(primary)
        secondary.normalize()
        tertiary = primary.cross(secondary).normalized()
    else:
        secondary = pairs[1][1]
        tertiary = primary.cross(secondary).normalized()

    # Local Y is the primary axis (largest variance).
    return _normalize_axes((secondary, primary, tertiary)) or _WORLD_AXES


def align_longest_to_z(axes, sizes):
    """Permute axes/sizes so the longest extent is local Z. Keep right-handed."""
    longest = max(range(3), key=lambda i: sizes[i])
    if longest == 2:
        return axes, sizes
    if longest == 0:
        order = (1, 2, 0)
    else:
        order = (2, 0, 1)
    return tuple(axes[i] for i in order), [sizes[i] for i in order]


def capsule_dimensions(sizes):
    height = sizes[2]
    radius = 0.5 * max(sizes[0], sizes[1], MIN_SIZE * 2)
    cyl_length = max(0.0, height - 2.0 * radius)
    return radius, cyl_length
