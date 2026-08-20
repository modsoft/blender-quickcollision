"""Headless Blender smoke test for registration and collider creation."""

from pathlib import Path
import sys

import bpy
from mathutils import Euler


PROJECT_PARENT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_PARENT))

bpy.ops.preferences.addon_enable(module="quickcollision")

bpy.ops.mesh.primitive_cube_add(location=(1.0, 2.0, 3.0))
source = bpy.context.object
source.name = "TestSource"
source.rotation_euler = Euler((0.35, -0.6, 0.2))
source.scale = (0.3, 0.3, 4.5)
bpy.context.view_layer.update()

collider_types = (
    "BOX_WORLD",
    "BOX_TRANSFORM",
    "BOX_EIGEN2",
    "BOX_EIGEN3",
    "CAPSULE_WORLD",
    "CAPSULE_TRANSFORM",
    "CAPSULE_EIGEN",
    "SPHERE",
    "CONVEX",
)


def create(collider_type, parent_to_source):
    preferences = bpy.context.preferences.addons["quickcollision"].preferences
    preferences.parent_to_source = parent_to_source
    bpy.ops.object.select_all(action="DESELECT")
    source.select_set(True)
    bpy.context.view_layer.objects.active = source
    result = bpy.ops.quickcollision.create(collider_type=collider_type)
    assert result == {"FINISHED"}, (collider_type, result)
    return bpy.context.object


def world_vertices(obj):
    return [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]


def assert_encloses(collider, points, tolerance=1e-5):
    inverse = collider.matrix_world.inverted_safe()
    local_points = [inverse @ point for point in points]
    collider_points = [vertex.co for vertex in collider.data.vertices]
    for axis in range(3):
        lower = min(point[axis] for point in collider_points) - tolerance
        upper = max(point[axis] for point in collider_points) + tolerance
        assert all(lower <= point[axis] <= upper for point in local_points), (
            collider.name,
            axis,
            lower,
            upper,
        )


for collider_type in collider_types:
    unparented = create(collider_type, False)
    expected = world_vertices(unparented)
    bpy.data.objects.remove(unparented, do_unlink=True)

    parented = create(collider_type, True)
    actual = world_vertices(parented)
    assert len(actual) == len(expected), collider_type
    error = max((left - right).length for left, right in zip(expected, actual))
    assert error < 1e-5, (collider_type, error)
    bpy.data.objects.remove(parented, do_unlink=True)

source_points = world_vertices(source)
for collider_type in ("BOX_WORLD", "BOX_TRANSFORM", "BOX_EIGEN2", "BOX_EIGEN3"):
    box = create(collider_type, True)
    assert_encloses(box, source_points)
    bpy.data.objects.remove(box, do_unlink=True)


for collider_type in collider_types:
    collider = create(collider_type, True)
    assert collider is not source, collider_type
    assert collider.parent == source, collider_type
    assert collider.users_collection[0].name == "Colliders", collider_type
    assert len(collider.data.vertices) > 0, collider_type


# Convex hull from an Edit Mode component selection.
def select_source_verts(indices):
    import bmesh

    bpy.ops.object.select_all(action="DESELECT")
    source.select_set(True)
    bpy.context.view_layer.objects.active = source
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_mode(type="VERT")
    bm = bmesh.from_edit_mesh(source.data)
    bm.verts.ensure_lookup_table()
    for vert in bm.verts:
        vert.select_set(vert.index in indices)
    bm.select_flush_mode()
    bmesh.update_edit_mesh(source.data)


# Four non-coplanar cube corners make a tetrahedron: 4 triangles.
select_source_verts({0, 1, 2, 4})
result = bpy.ops.quickcollision.create(collider_type="CONVEX")
assert result == {"FINISHED"}, result
hull = bpy.context.object
assert hull.name.startswith("UCX_"), hull.name
assert len(hull.data.vertices) == 4, len(hull.data.vertices)
assert len(hull.data.polygons) == 4, len(hull.data.polygons)
expected_corners = {
    tuple(round(value, 4) for value in source.matrix_world @ source.data.vertices[i].co)
    for i in (0, 1, 2, 4)
}
hull_corners = {
    tuple(round(value, 4) for value in vertex) for vertex in world_vertices(hull)
}
assert hull_corners == expected_corners, (hull_corners, expected_corners)
bpy.data.objects.remove(hull, do_unlink=True)

# A flat component selection must fail with a clear error, not a broken hull.
select_source_verts({0, 1, 2, 3})  # one cube face
try:
    bpy.ops.quickcollision.create(collider_type="CONVEX")
except RuntimeError as exc:
    assert "flat or collinear" in str(exc), exc
else:
    raise AssertionError("Flat selection should have been rejected")
bpy.ops.object.mode_set(mode="OBJECT")

# UE-style auto numbering: same prefix and source count up from _00.
assert "UCX_TestSource_00" in bpy.data.objects, sorted(o.name for o in bpy.data.objects)
second = create("CONVEX", True)
assert second.name == "UCX_TestSource_01", second.name
third = create("CONVEX", True)
assert third.name == "UCX_TestSource_02", third.name
bpy.data.objects.remove(second, do_unlink=True)
bpy.data.objects.remove(third, do_unlink=True)

# The wireframe toggle applies to new and existing colliders.
preferences = bpy.context.preferences.addons["quickcollision"].preferences
existing = bpy.data.objects["UCX_TestSource_00"]
preferences.wire_display = True
assert existing.display_type == "WIRE", existing.display_type
wired = create("CONVEX", True)
assert wired.display_type == "WIRE", wired.display_type
preferences.wire_display = False
assert existing.display_type == "TEXTURED", existing.display_type
assert wired.display_type == "TEXTURED", wired.display_type
bpy.data.objects.remove(wired, do_unlink=True)

# StanHull keeps dense meshes inside the vertex budget.
from quickcollision import stanhull

if stanhull.available():
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=2.0)
    dense = bpy.context.object
    dense.name = "DenseSource"

    def dense_hull():
        bpy.ops.object.select_all(action="DESELECT")
        dense.select_set(True)
        bpy.context.view_layer.objects.active = dense
        result = bpy.ops.quickcollision.create(collider_type="CONVEX")
        assert result == {"FINISHED"}, result
        return bpy.context.object

    for budget in (16, 32, 64):
        preferences.convex_max_verts = budget
        hull = dense_hull()
        vert_count = len(hull.data.vertices)
        assert 4 <= vert_count <= budget, (budget, vert_count)
        bpy.data.objects.remove(hull, do_unlink=True)
    preferences.convex_max_verts = 32

    # Skin width inflates the hull past the source surface.
    tight = dense_hull()
    tight_radius = max(vertex.co.length for vertex in tight.data.vertices)
    assert tight_radius <= 2.01, tight_radius
    bpy.data.objects.remove(tight, do_unlink=True)

    preferences.convex_skin_width = 0.2
    inflated = dense_hull()
    inflated_radius = max(vertex.co.length for vertex in inflated.data.vertices)
    assert inflated_radius > 2.05, inflated_radius
    assert len(inflated.data.vertices) <= 32, len(inflated.data.vertices)
    bpy.data.objects.remove(inflated, do_unlink=True)
    preferences.convex_skin_width = 0.0

    bpy.data.objects.remove(dense, do_unlink=True)
    print("QUICKCOLLISION_STANHULL_OK")
else:
    print("QUICKCOLLISION_STANHULL_SKIPPED (DLL not built)")

print(f"QUICKCOLLISION_OPERATORS_OK {len(collider_types)}")
bpy.ops.preferences.addon_disable(module="quickcollision")
