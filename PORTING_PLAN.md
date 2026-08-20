# Quick Collision implementation plan

Quick Collision is a native Blender add-on built from scratch with `bpy`,
`bmesh`, and `mathutils`. The target is Blender 4.2 and newer.

## Product decisions

- The add-on lives as its own project under `projects/blender/quickcollision`.
- UI lives in **3D Viewport → Sidebar → Quick Collision**.
- Blender's built-in icons are used.
- New colliders are parented to the active source mesh by default. This can be
  disabled in the panel or add-on preferences.
- New colliders are moved to a `Colliders` collection by default. Both the
  behavior and collection name are configurable.
- Default names use common game-engine prefixes: `UBX_`, `USP_`, `UCP_`, and
  `UCX_`.
- Object Mode fits all evaluated vertices of selected meshes. Edit Mode fits
  selected vertices and the vertices belonging to selected edges or faces.

## Current scaffold

- Extension manifest and legacy `bl_info`
- Register/unregister lifecycle
- Add-on preferences and sidebar controls
- One undoable creation operator with nine creation modes
- World-space selection sampling
- Box, sphere, capsule, and native BMesh convex-hull creation
- World, source-transform, two-axis, and three-axis fitting
- Collider material and viewport color
- Parenting, collection placement, unique naming, and convex triangle count

The current implementation is an initial functional scaffold. Each fitting mode
still needs focused validation against transformed and pathological meshes.

## Phase 1 — scaffold validation

1. Confirm clean enable/disable/reload in Blender 4.2 and 5.2.
2. Confirm the panel and every built-in icon render without console warnings.
3. Verify undo/redo in Object Mode and single/multi-object Edit Mode.
4. Verify preferences persist across Blender sessions.
5. Add a development junction from the shared Blender add-ons folder if desired.

Exit condition: the add-on can be installed, enabled, reloaded, and removed
without errors.

## Phase 2 — selection contract

1. Test active-object selection and multiple selected objects.
2. Test vertex, edge, and face selection in Edit Mode.
3. Decide whether multi-object input produces one combined collider or one
   collider per source. The scaffold currently creates one combined collider
   named and parented from the active source.
4. Test evaluated geometry from common modifiers.
5. Define behavior for empty meshes, loose geometry, curves, and non-mesh
   selections.

Exit condition: selection behavior is explicit, predictable, and covered by a
small manual test matrix.

## Phase 3 — fit accuracy

1. Validate world- and source-aligned bounds under rotation, non-uniform scale,
   negative scale, and unapplied transforms.
2. Validate two-axis and three-axis covariance fits for long, flat, symmetric,
   and nearly degenerate shapes.
3. Stabilize covariance axis signs where repeated execution can otherwise flip
   orientation.
4. Add numerical fallbacks for collinear and coplanar point sets.
5. Compare all bounds against the source points to ensure no point falls outside.

Exit condition: all primitive colliders enclose their input and produce stable
orientation on repeated runs.

## Phase 4 — primitive quality

1. Tune sphere, capsule, and convex tessellation for viewport and export use.
2. Confirm capsule dimensions enclose the fitted bounds in every orientation.
3. Validate convex hulls for duplicate, coplanar, and collinear points.
4. Confirm displayed convex triangle count matches the triangulated export count.
5. Decide whether the 255-triangle threshold remains fixed or becomes a setting.

Exit condition: generated meshes are manifold, have outward normals, and report
useful convex complexity.

## Phase 5 — workflow polish

1. Preserve or intentionally replace selection and mode after creation.
2. Review naming and numbering behavior for repeated colliders.
3. Add clear operator reports for invalid input and degenerate geometry.
4. Test collection behavior in linked, nested, and multi-scene files.
5. Write a concise manual test checklist and package-install instructions.

Exit condition: the add-on is ready for routine artist testing.

## Verification approach

- Static compile all Python modules outside Blender.
- Run Blender 5.2 headlessly to enable/register the add-on.
- Run a headless smoke script that creates transformed meshes and invokes each
  collider mode.
- Perform interactive checks for panel layout, component selection, undo, and
  viewport appearance.
