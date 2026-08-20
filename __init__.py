# SPDX-License-Identifier: MIT

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

import importlib
import os
import re

from . import constants
from . import stanhull
from . import geometry
from . import primitives
from . import operators
from . import properties
from . import ui

# Re-import submodules on enable so toggling the add-on picks up edits.
# Turn this off for a release build.
DEV_RELOAD = True

_support = (
    constants,
    stanhull,
    geometry,
    primitives,
)

_modules = (
    properties,
    operators,
    ui,
)


def _reload():
    for mod in _support + _modules:
        importlib.reload(mod)


def _check_manifest_version():
    """bl_info and blender_manifest.toml carry the version separately."""
    path = os.path.join(os.path.dirname(__file__), "blender_manifest.toml")
    try:
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
    except OSError:
        return

    for key, expected in (
        ("version", ".".join(str(part) for part in bl_info["version"])),
        ("blender_version_min", ".".join(str(part) for part in bl_info["blender"])),
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
    if DEV_RELOAD:
        _reload()
    _check_manifest_version()
    for mod in _modules:
        mod.register()


def unregister():
    for mod in reversed(_modules):
        mod.unregister()
