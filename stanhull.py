# SPDX-License-Identifier: MIT

"""ctypes bridge to the vendored StanHull DLL (see native/).

StanHull builds an approximating convex hull with a vertex budget,
unlike Blender's exact hull. When the DLL is missing (unbuilt checkout
or non-Windows platform) callers fall back to bmesh.ops.convex_hull.
"""

import ctypes
import os
import platform

_DLL_NAMES = {
    ("Windows", "AMD64"): "stanhull-win64.dll",
}

_dll = None
_load_attempted = False


def _load():
    global _dll, _load_attempted
    if _load_attempted:
        return _dll
    _load_attempted = True

    name = _DLL_NAMES.get((platform.system(), platform.machine()))
    if name is None:
        return None
    path = os.path.join(os.path.dirname(__file__), name)
    if not os.path.isfile(path):
        return None

    try:
        dll = ctypes.CDLL(path)
        dll.stanhull_build.restype = ctypes.c_int
        dll.stanhull_build.argtypes = (
            ctypes.POINTER(ctypes.c_float),
            ctypes.c_uint,
            ctypes.c_uint,
            ctypes.c_float,
            ctypes.POINTER(ctypes.POINTER(ctypes.c_float)),
            ctypes.POINTER(ctypes.c_uint),
            ctypes.POINTER(ctypes.POINTER(ctypes.c_uint)),
            ctypes.POINTER(ctypes.c_uint),
        )
        dll.stanhull_free.restype = None
        dll.stanhull_free.argtypes = (
            ctypes.POINTER(ctypes.c_float),
            ctypes.POINTER(ctypes.c_uint),
        )
    except OSError:
        return None

    _dll = dll
    return _dll


def available():
    return _load() is not None


def build_hull(points, max_verts, skin_width=0.0):
    """Simplified convex hull of an iterable of 3d points.

    Returns (verts, tris) where verts is a list of (x, y, z) tuples and
    tris is a list of (a, b, c) index tuples, or None on failure.
    """
    dll = _load()
    if dll is None:
        return None

    flat = []
    for point in points:
        flat.extend((point[0], point[1], point[2]))
    count = len(flat) // 3
    if count < 4:
        return None

    in_arr = (ctypes.c_float * len(flat))(*flat)
    out_verts = ctypes.POINTER(ctypes.c_float)()
    out_vert_count = ctypes.c_uint()
    out_tris = ctypes.POINTER(ctypes.c_uint)()
    out_tri_count = ctypes.c_uint()

    rc = dll.stanhull_build(
        in_arr,
        count,
        max(int(max_verts), 0),
        ctypes.c_float(skin_width),
        ctypes.byref(out_verts),
        ctypes.byref(out_vert_count),
        ctypes.byref(out_tris),
        ctypes.byref(out_tri_count),
    )
    if rc != 0:
        return None

    try:
        verts = [
            (out_verts[i * 3], out_verts[i * 3 + 1], out_verts[i * 3 + 2])
            for i in range(out_vert_count.value)
        ]
        tris = [
            (out_tris[i * 3], out_tris[i * 3 + 1], out_tris[i * 3 + 2])
            for i in range(out_tri_count.value)
        ]
    finally:
        dll.stanhull_free(out_verts, out_tris)

    if len(verts) < 4 or not tris:
        return None
    return verts, tris
