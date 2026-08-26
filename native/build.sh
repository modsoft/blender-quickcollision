#!/usr/bin/env bash
# Builds stanhull-linux64.so. Requires g++ (sudo apt install g++).
set -euo pipefail

nativeDir="$(cd "$(dirname "$0")" && pwd)"
if [[ -f "$nativeDir/../stanhull.py" ]]; then
  out="$nativeDir/../stanhull-linux64.so"
else
  out="$nativeDir/stanhull-linux64.so"
fi

cxx="${CXX:-g++}"
"$cxx" -O2 -std=c++11 -fPIC -fvisibility=hidden -shared \
  -I "$nativeDir" \
  "$nativeDir/stanhull.cpp" \
  "$nativeDir/stanhull_capi.cpp" \
  -o "$out"

echo "Built $out"
