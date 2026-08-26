# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.types import Panel

from . import icons
from .kinds import KINDS, family
from .properties import prefs


def _settings(layout, context):
    try:
        return prefs(context)
    except RuntimeError:
        layout.label(text="Reload Quick Collision to finish enabling.")
        return None


def _compact_enabled(context):
    try:
        return prefs(context).compact_view
    except RuntimeError:
        return False


def _draw_create_button(layout, kind, compact=False):
    custom = icons.icon_id(kind.id)
    op = layout.operator(
        "quickcollision.create",
        text=kind.compact if compact else kind.short,
        icon_value=custom,
        icon=kind.builtin_icon if custom == 0 else "NONE",
    )
    op.collider_type = kind.id


def _draw_type_buttons(layout, kinds):
    column = layout.column(align=True)
    for kind in kinds:
        _draw_create_button(column, kind)


def _draw_compact_grid(layout, settings):
    grid = layout.grid_flow(
        row_major=True,
        columns=3,
        even_columns=True,
        even_rows=True,
        align=True,
    )
    for kind in KINDS:
        _draw_create_button(grid, kind, compact=True)
    column = layout.column(align=True)
    column.prop(settings, "convex_max_verts")
    column.prop(settings, "convex_skin_width")


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
        layout = self.layout
        settings = _settings(layout, context)
        if settings is None:
            return
        if settings.compact_view:
            _draw_compact_grid(layout, settings)


class _SectionPanel:
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Quick Collision"
    bl_parent_id = "QUICKCOLLISION_PT_main"


class _ExpandedSection(_SectionPanel):
    @classmethod
    def poll(cls, context):
        return not _compact_enabled(context)


class QUICKCOLLISION_PT_box(_ExpandedSection, Panel):
    bl_label = "Box"
    bl_idname = "QUICKCOLLISION_PT_box"

    def draw(self, context):
        layout = self.layout
        settings = _settings(layout, context)
        if settings is None:
            return
        box = layout.box()
        _draw_type_buttons(box, family("box"))
        _draw_prefix(box, settings, "box_prefix")


class QUICKCOLLISION_PT_capsule(_ExpandedSection, Panel):
    bl_label = "Capsule"
    bl_idname = "QUICKCOLLISION_PT_capsule"

    def draw(self, context):
        layout = self.layout
        settings = _settings(layout, context)
        if settings is None:
            return
        box = layout.box()
        _draw_type_buttons(box, family("capsule"))
        _draw_prefix(box, settings, "capsule_prefix")


class QUICKCOLLISION_PT_sphere(_ExpandedSection, Panel):
    bl_label = "Sphere"
    bl_idname = "QUICKCOLLISION_PT_sphere"

    def draw(self, context):
        layout = self.layout
        settings = _settings(layout, context)
        if settings is None:
            return
        box = layout.box()
        _draw_type_buttons(box, family("sphere"))
        _draw_prefix(box, settings, "sphere_prefix")


class QUICKCOLLISION_PT_convex(_ExpandedSection, Panel):
    bl_label = "Convex"
    bl_idname = "QUICKCOLLISION_PT_convex"

    def draw(self, context):
        layout = self.layout
        settings = _settings(layout, context)
        if settings is None:
            return
        box = layout.box()
        _draw_type_buttons(box, family("convex"))
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
        box.prop(settings, "compact_view")
        box.prop(settings, "parent_to_source")
        row = box.row(align=True)
        row.prop(settings, "use_collection")
        sub = row.row(align=True)
        sub.enabled = settings.use_collection
        sub.prop(settings, "collection_name", text="")
        box.prop(settings, "wire_display")
        box.prop(settings, "suffix", text="Suffix")
        if settings.compact_view:
            box.separator()
            box.prop(settings, "box_prefix", text="Box")
            box.prop(settings, "capsule_prefix", text="Capsule")
            box.prop(settings, "sphere_prefix", text="Sphere")
            box.prop(settings, "convex_prefix", text="Convex")


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
