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

print(f"QUICKCOLLISION_OPERATORS_OK {len(collider_types)}")
bpy.ops.preferences.addon_disable(module="quickcollision")
