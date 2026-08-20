# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
# ##### END GPL LICENSE BLOCK #####

import bpy
from bpy.types import Panel

from .constants import MAX_CONVEX_TRIS
from .operators import COLLIDER_TYPES
from .properties import prefs


def _draw_type_buttons(layout, types):
    column = layout.column(align=True)
    for collider_type, label, _tip, icon, _idx in types:
        op = column.operator("quickcollision.create", text=label, icon=icon)
        op.collider_type = collider_type


class QUICKCOLLISION_PT_main(Panel):
    bl_label = "Quick Collision"
    bl_idname = "QUICKCOLLISION_PT_main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Quick Collision"

    def draw(self, context):
        layout = self.layout
        try:
            settings = prefs(context)
        except RuntimeError:
            layout.label(text="Reload Quick Collision to finish enabling.")
            return

        layout.prop(settings, "parent_to_source")
        row = layout.row(align=True)
        row.prop(settings, "use_collection")
        sub = row.row(align=True)
        sub.enabled = settings.use_collection
        sub.prop(settings, "collection_name", text="")

        layout.separator()

        col = layout.column(align=True)
        col.prop(settings, "box_prefix", text="Box")
        _draw_type_buttons(col, COLLIDER_TYPES[0:4])

        col = layout.column(align=True)
        col.prop(settings, "capsule_prefix", text="Capsule")
        _draw_type_buttons(col, COLLIDER_TYPES[4:7])

        col = layout.column(align=True)
        col.prop(settings, "sphere_prefix", text="Sphere")
        _draw_type_buttons(col, COLLIDER_TYPES[7:8])

        col = layout.column(align=True)
        col.prop(settings, "convex_prefix", text="Convex")
        op = col.operator("quickcollision.create", text="Convex", icon="CONVEXHULL")
        op.collider_type = "CONVEX"
        tris = context.window_manager.quickcollision_last_tris
        if tris > MAX_CONVEX_TRIS:
            col.label(text=f"{tris} triangles", icon="ERROR")
        else:
            col.label(text=f"{tris:02d} triangles")

        layout.prop(settings, "suffix", text="Suffix")


classes = (QUICKCOLLISION_PT_main,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
