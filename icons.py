# SPDX-License-Identifier: MIT

"""Custom UI icons. Drop replacement 64x64 RGBA PNGs into icons/ using the same filenames."""

import os

import bpy

from .kinds import KINDS

ICON_NAMES = tuple(kind.id for kind in KINDS)

_preview = None


def icon_id(name):
    if _preview is None or name not in _preview:
        return 0
    return _preview[name].icon_id


def register():
    global _preview
    if _preview is not None:
        return
    _preview = bpy.utils.previews.new()
    folder = os.path.join(os.path.dirname(__file__), "icons")
    for name in ICON_NAMES:
        path = os.path.join(folder, f"{name}.png")
        if os.path.isfile(path):
            _preview.load(name, path, "IMAGE", force_reload=True)


def unregister():
    global _preview
    if _preview is None:
        return
    bpy.utils.previews.remove(_preview)
    _preview = None
