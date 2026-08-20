# Blender QuickCollision

Quickly generate game engine compliant collision meshes.

Generate box, sphere, capsule, and convex colliders from any object or Edit Mode selection
Automatic Unreal Engine standard naming convention (`UBX_`, `USP_`, `UCP_`, `UCX_`) and suffix numbering `_00`, `_01`,...
Colliders can be auto-parented to their source, gathered into a dedicated collection, and displayed as wireframe. 

**Convex generation generated with an implementation of StanHull** — Stan Melax's approximating hull algorithm from the PhysX toolchain.
(Credit to Stan Melax and John Ratcliff.)

<img width="165" height="430" alt="image" src="https://github.com/user-attachments/assets/a450c914-7a87-4fab-aa92-1cf2b6e94933" />

<img width="1310" height="556" alt="image" src="https://github.com/user-attachments/assets/d5d1569f-2a8e-4bd6-917d-fdb091f6d343" />


## Install

Download the zip and install it from **Edit → Preferences → Add-ons → Install from Disk**. The tools are in the **Quick Collision** tab of the 3D Viewport
sidebar.

Blender 4.2 or newer is required.

## License

MIT. See [LICENSE](LICENSE). The vendored StanHull sources in `native/` are BSD-3 licensed (Open Dynamics Framework Group); see `native/LICENSE`.
