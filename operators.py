# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.props import EnumProperty
from bpy.types import Operator

from . import geometry, primitives
from .constants import MAX_CONVEX_TRIS
from .kinds import BY_ID, enum_items
from .properties import prefs

COLLIDER_TYPES = enum_items()


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
        kind = BY_ID.get(properties.collider_type)
        if kind is None:
            return cls.bl_label
        if kind.tip:
            return f"{kind.label}\n{kind.tip}"
        return kind.label

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
        prefix = getattr(settings, BY_ID[self.collider_type].prefix_attr)
        name = primitives.collider_name(prefix, source.name, settings.suffix)

        try:
            obj, hull_stats = self._create(context, points, source, name, settings)
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        primitives.apply_collider_look(obj, settings.wire_display)

        if settings.parent_to_source:
            primitives.parent_keep_world(obj, source)

        if settings.use_collection and settings.collection_name.strip():
            col = primitives.ensure_collection(context.scene, settings.collection_name.strip())
            primitives.move_to_collection(obj, col)

        primitives.select_only(context, obj)

        if hull_stats is not None:
            vert_count, tri_count = hull_stats
            if tri_count > MAX_CONVEX_TRIS:
                self.report(
                    {"WARNING"},
                    f"Convex collider has {tri_count} triangles (limit {MAX_CONVEX_TRIS})",
                )
            else:
                self.report(
                    {"INFO"},
                    f"Convex collider: {vert_count} verts, {tri_count} triangles",
                )
        else:
            self.report({"INFO"}, f"Created {obj.name}")

        return {"FINISHED"}

    def _create(self, context, points, source, name, settings):
        kind = self.collider_type

        if kind == "SPHERE":
            center = geometry.aabb_center(points)
            radius = geometry.furthest_distance(center, points)
            return primitives.make_sphere(context, name, center, radius), None

        if kind == "CONVEX":
            if len(points) < 3:
                raise RuntimeError("Convex hull needs at least 3 points")
            return primitives.make_convex(
                context,
                name,
                points,
                settings.convex_max_verts,
                settings.convex_skin_width,
            )

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
