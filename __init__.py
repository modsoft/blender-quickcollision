# SPDX-License-Identifier: GPL-3.0-or-later

bl_info = {
    "name": "Quick Collision",
    "author": "Trey",
    "version": (0, 1, 0),
    "blender": (4, 2, 0),
    "location": "3D Viewport > Sidebar > Quick Collision",
    "doc_url": "https://github.com/modsoft/blender-quickcollision",
    "description": "Create box, sphere, capsule, and convex colliders for game engines",
    "category": "3D View",
}

# Blender deletes module.bl_info when this is loaded as an extension, then
# calls register(). Keep a copy for the manifest version check.
_BL_INFO = dict(bl_info)

_needs_reload = "bpy" in locals()

import os
import re

import bpy
from . import (
    constants,
    kinds,
    stanhull,
    hull,
    geometry,
    primitives,
    icons,
    operators,
    properties,
    ui,
)

if _needs_reload:
    import importlib

    constants = importlib.reload(constants)
    kinds = importlib.reload(kinds)
    stanhull = importlib.reload(stanhull)
    hull = importlib.reload(hull)
    geometry = importlib.reload(geometry)
    primitives = importlib.reload(primitives)
    icons = importlib.reload(icons)
    operators = importlib.reload(operators)
    properties = importlib.reload(properties)
    ui = importlib.reload(ui)
    print("Quick Collision reloaded")

_modules = (
    properties,
    operators,
    ui,
)


def _check_manifest_version():
    """bl_info and blender_manifest.toml carry the version separately."""
    path = os.path.join(os.path.dirname(__file__), "blender_manifest.toml")
    try:
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
    except OSError:
        return

    for key, expected in (
        ("version", ".".join(str(part) for part in _BL_INFO["version"])),
        ("blender_version_min", ".".join(str(part) for part in _BL_INFO["blender"])),
    ):
        match = re.search(rf'^{key}\s*=\s*"([^"]+)"', text, re.MULTILINE)
        if match and match.group(1) != expected:
            print(
                f"Quick Collision: blender_manifest.toml {key} is {match.group(1)}, "
                f"bl_info says {expected}"
            )


def register():
    try:
        unregister()
    except Exception:
        pass
    _check_manifest_version()
    icons.register()
    for mod in _modules:
        mod.register()


def unregister():
    for mod in reversed(_modules):
        mod.unregister()
    icons.unregister()
