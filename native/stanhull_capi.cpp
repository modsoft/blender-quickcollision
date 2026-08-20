// SPDX-License-Identifier: MIT
// Flat C API around StanHull for ctypes.
// StanHull itself is BSD-3 licensed, see LICENSE in this folder.

#include "stanhull.h"

#include <cstring>

extern "C" {

// Builds a simplified convex hull from an xyz float array.
// Returns 0 on success. Output arrays must be released with stanhull_free.
__declspec(dllexport) int stanhull_build(
    const float *points,
    unsigned int point_count,
    unsigned int max_verts,
    float skin_width,
    float **out_verts,
    unsigned int *out_vert_count,
    unsigned int **out_tris,
    unsigned int *out_tri_count)
{
    *out_verts = nullptr;
    *out_vert_count = 0;
    *out_tris = nullptr;
    *out_tri_count = 0;

    if (points == nullptr || point_count < 4) {
        return 1;
    }

    StanHull::HullDesc desc;
    desc.SetHullFlag(StanHull::QF_TRIANGLES);
    desc.mVcount = point_count;
    desc.mVertices = points;
    desc.mVertexStride = sizeof(float) * 3;
    desc.mMaxVertices = max_verts > 0 ? max_verts : 4096;
    if (skin_width > 0.0f) {
        desc.SetHullFlag(StanHull::QF_SKIN_WIDTH);
        desc.mSkinWidth = skin_width;
    } else {
        desc.mSkinWidth = 0.0f;
    }

    StanHull::HullResult result;
    StanHull::HullLibrary library;
    if (library.CreateConvexHull(desc, result) != StanHull::QE_OK) {
        library.ReleaseResult(result);
        return 2;
    }

    const unsigned int vert_floats = result.mNumOutputVertices * 3;
    const unsigned int index_count = result.mNumFaces * 3;
    float *verts = new float[vert_floats];
    unsigned int *tris = new unsigned int[index_count];
    std::memcpy(verts, result.mOutputVertices, vert_floats * sizeof(float));
    std::memcpy(tris, result.mIndices, index_count * sizeof(unsigned int));

    *out_verts = verts;
    *out_vert_count = result.mNumOutputVertices;
    *out_tris = tris;
    *out_tri_count = result.mNumFaces;

    library.ReleaseResult(result);
    return 0;
}

__declspec(dllexport) void stanhull_free(float *verts, unsigned int *tris)
{
    delete[] verts;
    delete[] tris;
}

}  // extern "C"
