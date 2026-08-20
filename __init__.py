# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Quick Collision",
    "author": "Trey",
    "version": (0, 1, 0),
    "blender": (4, 2, 0),
    "location": "3D Viewport > Sidebar > Quick Collision",
    "description": "Create box, sphere, capsule, and convex colliders for game engines",
    "category": "3D View",
    "doc_url": "https://github.com/modsoft/blender-quickcollision",
}

import importlib

from . import constants
from . import geometry
from . import primitives
from . import operators
from . import properties
from . import ui

_modules = (
    properties,
    operators,
    ui,
)


def _reload():
    importlib.reload(constants)
    importlib.reload(geometry)
    importlib.reload(primitives)
    importlib.reload(properties)
    importlib.reload(operators)
    importlib.reload(ui)


def register():
    try:
        unregister()
    except Exception:
        pass
    _reload()
    for mod in _modules:
        mod.register()


def unregister():
    for mod in reversed(_modules):
        mod.unregister()
