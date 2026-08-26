# SPDX-License-Identifier: GPL-3.0-or-later

"""Collider kinds: one catalog for the operator enum, UI copy, prefixes, and icons."""

from collections import namedtuple

Kind = namedtuple(
    "Kind",
    "id label tip builtin_icon index family prefix_attr short compact",
)

KINDS = (
    Kind(
        "BOX_WORLD",
        "World Box",
        "Create a world-aligned box collider",
        "MESH_CUBE",
        0,
        "box",
        "box_prefix",
        "World",
        "World",
    ),
    Kind(
        "BOX_TRANSFORM",
        "Object Box",
        "Create a box collider aligned to the source object's axes",
        "ORIENTATION_LOCAL",
        1,
        "box",
        "box_prefix",
        "Object",
        "Object",
    ),
    Kind(
        "BOX_EIGEN2",
        "Fit Box 2-Axis",
        "Create a box collider aligned to the primary axis of the selection",
        "EMPTY_AXIS",
        2,
        "box",
        "box_prefix",
        "Fit 2-Axis",
        "Fit 2",
    ),
    Kind(
        "BOX_EIGEN3",
        "Fit Box 3-Axis",
        "Create a box collider aligned to the shape of the selection",
        "EMPTY_ARROWS",
        3,
        "box",
        "box_prefix",
        "Fit 3-Axis",
        "Fit 3",
    ),
    Kind(
        "CAPSULE_WORLD",
        "World Capsule",
        "Create a world-aligned capsule collider",
        "MESH_CAPSULE",
        4,
        "capsule",
        "capsule_prefix",
        "World",
        "World",
    ),
    Kind(
        "CAPSULE_TRANSFORM",
        "Object Capsule",
        "Create a capsule collider aligned to the source object's axes",
        "ORIENTATION_GIMBAL",
        5,
        "capsule",
        "capsule_prefix",
        "Object",
        "Object",
    ),
    Kind(
        "CAPSULE_EIGEN",
        "Fit Capsule",
        "Create a capsule collider aligned to the shape of the selection",
        "MOD_SIMPLEDEFORM",
        6,
        "capsule",
        "capsule_prefix",
        "Fit 3-Axis",
        "Fit",
    ),
    Kind(
        "SPHERE",
        "Sphere",
        "Create a sphere collider from the selection center",
        "MESH_UVSPHERE",
        7,
        "sphere",
        "sphere_prefix",
        "Sphere",
        "Sphere",
    ),
    Kind(
        "CONVEX",
        "Convex",
        "Create a convex hull collider from the selection",
        "MESH_ICOSPHERE",
        8,
        "convex",
        "convex_prefix",
        "Convex Hull",
        "Hull",
    ),
)

BY_ID = {kind.id: kind for kind in KINDS}


def enum_items():
    return tuple(
        (kind.id, kind.label, kind.tip, kind.builtin_icon, kind.index) for kind in KINDS
    )


def family(name):
    return tuple(kind for kind in KINDS if kind.family == name)
