# Blender QuickCollision

Quickly generate game engine compliant collision meshes.

<img width="1920" height="1080" alt="qc_splash" src="https://github.com/user-attachments/assets/b399522a-5375-4cda-95bf-346747222d14" />

# Features

- Generate box, sphere, capsule, and convex colliders from any object or Edit Mode selection
- Automatic Unreal Engine standard naming convention (`UBX_`, `USP_`, `UCP_`, `UCX_`) and suffix numbering `_00`, `_01`,...
- Colliders can be auto-parented to their source, gathered into a dedicated collection, and displayed as wireframe. 
- **Convex generation generated with an implementation of StanHull** — Stan Melax's approximating hull algorithm from the PhysX toolchain. (Credit to Stan Melax and John Ratcliff.)


<img width="1366" height="768" alt="previews_01" src="https://github.com/user-attachments/assets/2a26dd96-73a3-4975-9e76-026ecd5ed920" />


<img width="1366" height="768" alt="previews_02" src="https://github.com/user-attachments/assets/c8b122b6-7d2a-4d81-aa4f-36b6df841411" />


- **Compact UI Mode** `Settings > Compact View`

<img width="318" height="233" alt="image" src="https://github.com/user-attachments/assets/1f4c0e04-99cc-41f7-ad47-978046e728d6" />


## Install

Blender 4.2 or newer.

Check Releases or Code > Download Zip for latest.

Drag the zip onto Blender, or install from **Edit → Preferences → Get Extensions → Install from Disk**.
The tools are in the **Quick Collision** tab of the 3D Viewport sidebar.

## License

The add-on (Python) is **GPL-3.0-or-later**. See [LICENSE](LICENSE).

- **StanHull** (`native/`, `stanhull-win64.dll`, `stanhull-linux64.so`): BSD-3-Clause. See [native/LICENSE](native/LICENSE) and [NOTICE](NOTICE).
- **Icons** (`icons/*.png`): [CC0 1.0](icons/LICENSE).
