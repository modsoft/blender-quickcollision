# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
# ##### END GPL LICENSE BLOCK #####

import bpy
from bpy.props import BoolProperty, IntProperty, StringProperty
from bpy.types import AddonPreferences

from .constants import DEFAULT_COLLECTION, REPOSITORY_URL


class QuickCollisionPreferences(AddonPreferences):
    bl_idname = __package__

    box_prefix: StringProperty(
        name="Box Prefix",
        default="UBX_",
        description="Name prefix for box colliders",
    )
    sphere_prefix: StringProperty(
        name="Sphere Prefix",
        default="USP_",
        description="Name prefix for sphere colliders",
    )
    capsule_prefix: StringProperty(
        name="Capsule Prefix",
        default="UCP_",
        description="Name prefix for capsule colliders",
    )
    convex_prefix: StringProperty(
        name="Convex Prefix",
        default="UCX_",
        description="Name prefix for convex colliders",
    )
    suffix: StringProperty(
        name="Suffix",
        default="",
        description="Optional suffix appended to every collider name",
    )
    parent_to_source: BoolProperty(
        name="Parent to Source",
        default=True,
        description="Parent the collider to the source object, keeping world transform",
    )
    use_collection: BoolProperty(
        name="Add to Collection",
        default=True,
        description="Move created colliders into a dedicated collection",
    )
    collection_name: StringProperty(
        name="Collection",
        default=DEFAULT_COLLECTION,
        description="Collection that colliders are moved into",
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "parent_to_source")
        row = layout.row(align=True)
        row.prop(self, "use_collection")
        row.prop(self, "collection_name", text="")
        layout.separator()
        layout.prop(self, "box_prefix")
        layout.prop(self, "sphere_prefix")
        layout.prop(self, "capsule_prefix")
        layout.prop(self, "convex_prefix")
        layout.prop(self, "suffix")
        layout.separator()
        link = layout.operator("wm.url_open", text="GitHub Repository", icon="URL")
        link.url = REPOSITORY_URL


def prefs(context):
    addon = context.preferences.addons.get(__package__)
    if addon is None:
        raise RuntimeError("Quick Collision is not enabled")
    return addon.preferences


classes = (QuickCollisionPreferences,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.WindowManager.quickcollision_last_tris = IntProperty(
        name="Last Convex Tris",
        default=0,
        min=0,
    )


def unregister():
    if hasattr(bpy.types.WindowManager, "quickcollision_last_tris"):
        del bpy.types.WindowManager.quickcollision_last_tris
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
