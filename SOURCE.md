# Source and build information

Upstream source: https://github.com/overleaf/overleaf.git
Source revision: e039ad26c5bf5422eb57b89fc7e57c75055e631d
Local patch: texlive-full.patch
Patch SHA256: e4e655ccfa248fb6bd732b393e365bed6520cbcc8db17cd1ebf3ab2021892c20
Release image: ghcr.io/vishvish/overleaf-personal:2026-10-27@sha256:12fd54413f1ec5a3935bcdfcbe821810bde04d2dc9ed1cf27dfed2f56ea8836f

The upstream LICENSE is included. This is a community build using upstream's
server-ce Makefile with full TeX Live and Fontconfig registration enabled by
the included patch. No private projects, uploaded fonts or account data are
part of the image or this package.

To build from source (run in a new working directory with the patch alongside):

```sh
git clone https://github.com/overleaf/overleaf.git source
git -C source checkout e039ad26c5bf5422eb57b89fc7e57c75055e631d
git -C source apply ../texlive-full.patch
arch=arm64 # use amd64 for Intel / AMD
DOCKER_DEFAULT_PLATFORM="linux/$arch" make -C source/server-ce \
  OVERLEAF_BASE_TAG="overleaf-local-base:$arch" \
  OVERLEAF_BASE_BRANCH="overleaf-local-base:$arch" \
  OVERLEAF_TAG="overleaf-local:$arch" \
  OVERLEAF_BRANCH="overleaf-local:$arch" build-base build-community
```

Building uses the current TeX Live mirror and OS package repositories.
The pinned release digest identifies the distributed binaries exactly.
