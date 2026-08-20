# SPDX-License-Identifier: MIT

import bpy
from bpy.props import BoolProperty, FloatProperty, IntProperty, StringProperty
from bpy.types import AddonPreferences

from .constants import DEFAULT_COLLECTION, MAT_NAME, REPOSITORY_URL


def _update_wire_display(self, context):
    """Flip display mode on every existing collider, not just new ones."""
    mat = bpy.data.materials.get(MAT_NAME)
    if mat is None:
        return
    display = "WIRE" if self.wire_display else "TEXTURED"
    for obj in bpy.data.objects:
        if obj.type == "MESH" and mat.name in obj.data.materials:
            obj.display_type = display


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
    convex_max_verts: IntProperty(
        name="Max Verts",
        default=32,
        min=4,
        soft_max=256,
        max=1024,
        description=(
            "Vertex budget for convex hulls. StanHull keeps the most "
            "shape-defining vertices and discards the rest"
        ),
    )
    convex_skin_width: FloatProperty(
        name="Skin Width",
        default=0.0,
        min=0.0,
        soft_max=1.0,
        subtype="DISTANCE",
        description=(
            "Inflate the convex hull outward by roughly this distance so the "
            "simplified hull still encloses the source surface"
        ),
    )
    suffix: StringProperty(
        name="Suffix",
        default="_00",
        description=(
            "Suffix appended to every collider name. A numeric suffix like "
            "_00 counts up automatically when the name is already taken"
        ),
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
    wire_display: BoolProperty(
        name="Wireframe Display",
        default=False,
        update=_update_wire_display,
        description="Show colliders as wireframe so they never hide the source mesh",
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "parent_to_source")
        row = layout.row(align=True)
        row.prop(self, "use_collection")
        row.prop(self, "collection_name", text="")
        layout.prop(self, "wire_display")
        layout.separator()
        layout.prop(self, "box_prefix")
        layout.prop(self, "sphere_prefix")
        layout.prop(self, "capsule_prefix")
        layout.prop(self, "convex_prefix")
        layout.prop(self, "convex_max_verts")
        layout.prop(self, "convex_skin_width")
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


def unregister():
    # Clean up readout properties left behind by older versions.
    for attr in ("quickcollision_last_tris", "quickcollision_last_verts"):
        if hasattr(bpy.types.WindowManager, attr):
            delattr(bpy.types.WindowManager, attr)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
