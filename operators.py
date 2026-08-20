# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
# ##### END GPL LICENSE BLOCK #####

import bpy
from bpy.props import EnumProperty
from bpy.types import Operator

from . import geometry, primitives
from .constants import MAX_CONVEX_TRIS
from .properties import prefs

COLLIDER_TYPES = (
    (
        "BOX_WORLD",
        "World Box",
        "Create a world-aligned box collider",
        "MESH_CUBE",
        0,
    ),
    (
        "BOX_TRANSFORM",
        "Object Box",
        "Create a box collider aligned to the source object's axes",
        "ORIENTATION_LOCAL",
        1,
    ),
    (
        "BOX_EIGEN2",
        "Fit Box 2-Axis",
        "Create a box collider aligned to the primary axis of the selection",
        "EMPTY_AXIS",
        2,
    ),
    (
        "BOX_EIGEN3",
        "Fit Box 3-Axis",
        "Create a box collider aligned to the shape of the selection",
        "EMPTY_ARROWS",
        3,
    ),
    (
        "CAPSULE_WORLD",
        "World Capsule",
        "Create a world-aligned capsule collider",
        "MESH_CAPSULE",
        4,
    ),
    (
        "CAPSULE_TRANSFORM",
        "Object Capsule",
        "Create a capsule collider aligned to the source object's axes",
        "ORIENTATION_GIMBAL",
        5,
    ),
    (
        "CAPSULE_EIGEN",
        "Fit Capsule",
        "Create a capsule collider aligned to the shape of the selection",
        "MOD_SIMPLEDEFORM",
        6,
    ),
    (
        "SPHERE",
        "Sphere",
        "Create a sphere collider from the selection center",
        "MESH_UVSPHERE",
        7,
    ),
    (
        "CONVEX",
        "Convex",
        "Create a convex hull collider from the selection",
        "CONVEXHULL",
        8,
    ),
)

_PREFIX_ATTR = {
    "BOX_WORLD": "box_prefix",
    "BOX_TRANSFORM": "box_prefix",
    "BOX_EIGEN2": "box_prefix",
    "BOX_EIGEN3": "box_prefix",
    "CAPSULE_WORLD": "capsule_prefix",
    "CAPSULE_TRANSFORM": "capsule_prefix",
    "CAPSULE_EIGEN": "capsule_prefix",
    "SPHERE": "sphere_prefix",
    "CONVEX": "convex_prefix",
}


class QUICKCOLLISION_OT_create(Operator):
    bl_idname = "quickcollision.create"
    bl_label = "Create Collider"
    bl_options = {"REGISTER", "UNDO"}

    collider_type: EnumProperty(
        name="Type",
        items=COLLIDER_TYPES,
        default="BOX_WORLD",
    )

    @classmethod
    def poll(cls, context):
        return bool(geometry.mesh_objects(context))

    @classmethod
    def description(cls, context, properties):
        lookup = {item[0]: item[2] for item in COLLIDER_TYPES}
        return lookup.get(properties.collider_type, cls.bl_label)

    def execute(self, context):
        points = geometry.gather_points(context)
        if not points:
            self.report({"WARNING"}, "Select a mesh, or mesh components in Edit Mode")
            return {"CANCELLED"}

        source = geometry.source_object(context)
        if source is None:
            self.report({"WARNING"}, "No mesh object found")
            return {"CANCELLED"}

        settings = prefs(context)
        prefix = getattr(settings, _PREFIX_ATTR[self.collider_type])
        name = primitives.unique_object_name(f"{prefix}{source.name}{settings.suffix}")

        try:
            obj, tri_count = self._create(context, points, source, name)
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        primitives.apply_collider_look(obj)

        if settings.parent_to_source:
            primitives.parent_keep_world(obj, source)

        if settings.use_collection and settings.collection_name.strip():
            col = primitives.ensure_collection(context.scene, settings.collection_name.strip())
            primitives.move_to_collection(obj, col)

        primitives.select_only(context, obj)

        if tri_count is not None:
            context.window_manager.quickcollision_last_tris = tri_count
            if tri_count > MAX_CONVEX_TRIS:
                self.report(
                    {"WARNING"},
                    f"Convex collider has {tri_count} triangles (limit {MAX_CONVEX_TRIS})",
                )
            else:
                self.report({"INFO"}, f"Convex collider: {tri_count} triangles")
        else:
            self.report({"INFO"}, f"Created {obj.name}")

        return {"FINISHED"}

    def _create(self, context, points, source, name):
        kind = self.collider_type

        if kind == "SPHERE":
            center = geometry.aabb_center(points)
            radius = geometry.furthest_distance(center, points)
            return primitives.make_sphere(context, name, center, radius), None

        if kind == "CONVEX":
            if len(points) < 3:
                raise RuntimeError("Convex hull needs at least 3 points")
            return primitives.make_convex(context, name, points)

        if kind == "BOX_WORLD":
            axes = geometry.world_axes()
        elif kind == "BOX_TRANSFORM":
            axes = geometry.object_axes(source)
        elif kind == "BOX_EIGEN2":
            axes = geometry.covariance_axes(points, single_axis=True)
        elif kind == "BOX_EIGEN3":
            axes = geometry.covariance_axes(points, single_axis=False)
        elif kind == "CAPSULE_WORLD":
            axes = geometry.world_axes()
        elif kind == "CAPSULE_TRANSFORM":
            axes = geometry.object_axes(source)
        else:
            axes = geometry.covariance_axes(points, single_axis=True)

        matrix, sizes = geometry.oriented_bounds(points, axes)

        if kind.startswith("CAPSULE"):
            axes, sizes = geometry.align_longest_to_z(axes, sizes)
            matrix = geometry.matrix_from_axes(axes, matrix.translation)
            radius, cyl_length = geometry.capsule_dimensions(sizes)
            return primitives.make_capsule(context, name, matrix, radius, cyl_length), None

        return primitives.make_box(context, name, matrix, sizes), None


classes = (QUICKCOLLISION_OT_create,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
