# SPDX-License-Identifier: MIT

import bpy
from bpy.types import Panel

from .operators import COLLIDER_TYPES
from .properties import prefs


def _settings(layout, context):
    try:
        return prefs(context)
    except RuntimeError:
        layout.label(text="Reload Quick Collision to finish enabling.")
        return None


def _draw_type_buttons(layout, types):
    column = layout.column(align=True)
    for collider_type, label, _tip, icon, _idx in types:
        op = column.operator("quickcollision.create", text=label, icon=icon)
        op.collider_type = collider_type


def _draw_prefix(layout, settings, attr):
    row = layout.row(align=True)
    row.label(text="Prefix")
    row.prop(settings, attr, text="")


class QUICKCOLLISION_PT_main(Panel):
    bl_label = "Quick Collision"
    bl_idname = "QUICKCOLLISION_PT_main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Quick Collision"

    def draw(self, context):
        # Sections are sub-panels; the body only reports a bad enable state.
        try:
            prefs(context)
        except RuntimeError:
            self.layout.label(text="Reload Quick Collision to finish enabling.")


class _SectionPanel:
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Quick Collision"
    bl_parent_id = "QUICKCOLLISION_PT_main"


class QUICKCOLLISION_PT_box(_SectionPanel, Panel):
    bl_label = "Box"
    bl_idname = "QUICKCOLLISION_PT_box"

    def draw(self, context):
        layout = self.layout
        settings = _settings(layout, context)
        if settings is None:
            return
        box = layout.box()
        _draw_type_buttons(box, COLLIDER_TYPES[0:4])
        _draw_prefix(box, settings, "box_prefix")


class QUICKCOLLISION_PT_capsule(_SectionPanel, Panel):
    bl_label = "Capsule"
    bl_idname = "QUICKCOLLISION_PT_capsule"

    def draw(self, context):
        layout = self.layout
        settings = _settings(layout, context)
        if settings is None:
            return
        box = layout.box()
        _draw_type_buttons(box, COLLIDER_TYPES[4:7])
        _draw_prefix(box, settings, "capsule_prefix")


class QUICKCOLLISION_PT_sphere(_SectionPanel, Panel):
    bl_label = "Sphere"
    bl_idname = "QUICKCOLLISION_PT_sphere"

    def draw(self, context):
        layout = self.layout
        settings = _settings(layout, context)
        if settings is None:
            return
        box = layout.box()
        _draw_type_buttons(box, COLLIDER_TYPES[7:8])
        _draw_prefix(box, settings, "sphere_prefix")


class QUICKCOLLISION_PT_convex(_SectionPanel, Panel):
    bl_label = "Convex"
    bl_idname = "QUICKCOLLISION_PT_convex"

    def draw(self, context):
        layout = self.layout
        settings = _settings(layout, context)
        if settings is None:
            return
        box = layout.box()
        _draw_type_buttons(box, COLLIDER_TYPES[8:9])
        column = box.column(align=True)
        column.prop(settings, "convex_max_verts")
        column.prop(settings, "convex_skin_width")
        _draw_prefix(box, settings, "convex_prefix")


class QUICKCOLLISION_PT_settings(_SectionPanel, Panel):
    bl_label = "Settings"
    bl_idname = "QUICKCOLLISION_PT_settings"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        settings = _settings(layout, context)
        if settings is None:
            return
        box = layout.box()
        box.prop(settings, "parent_to_source")
        row = box.row(align=True)
        row.prop(settings, "use_collection")
        sub = row.row(align=True)
        sub.enabled = settings.use_collection
        sub.prop(settings, "collection_name", text="")
        box.prop(settings, "wire_display")
        box.prop(settings, "suffix", text="Suffix")


classes = (
    QUICKCOLLISION_PT_main,
    QUICKCOLLISION_PT_box,
    QUICKCOLLISION_PT_capsule,
    QUICKCOLLISION_PT_sphere,
    QUICKCOLLISION_PT_convex,
    QUICKCOLLISION_PT_settings,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
