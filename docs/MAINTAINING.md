# Maintaining the private release

The application image is published at `ghcr.io/vishvish/overleaf-personal`.
`release.lock` records its combined digest, architecture-specific digests,
upstream source revision, source patch checksum and database image references.
`image.txt` and `images.env` supply the same references to fresh installations.

Repository access and private-package access are separate permissions. Grant
friends **Read** access to the repository and to the GHCR package. They use their
own GitHub credentials for downloads and create their own Overleaf account on
their computer.

## Rebuild the application

Follow [SOURCE.md](../SOURCE.md) to check out the pinned public Overleaf source,
apply `texlive-full.patch` and use upstream's `server-ce` Makefile. Build once
with `arch=arm64` and once with `arch=amd64`. Use a local Docker engine; OrbStack
can emulate AMD64 when building on Apple Silicon.

Building full TeX Live takes time and uses substantial disk space. Builds use
the current OS repositories and TeX Live mirror. The source revision and patch
are pinned; exact distributed binary identity comes from the image digests.

Tag and push each checked platform image. For example, after the source build
in `SOURCE.md` has created `overleaf-local:arm64`:

```sh
release=2026-10-27
arch=arm64 # repeat with amd64 after building that variant
image_repo=ghcr.io/vishvish/overleaf-personal
docker tag "overleaf-local:$arch" "$image_repo:$release-$arch"
docker push --platform "linux/$arch" "$image_repo:$release-$arch"
```

Then publish the combined index:

```sh
docker buildx imagetools create \
  --tag "$image_repo:$release" \
  --tag "$image_repo:latest" \
  "$image_repo:${release}-arm64" \
  "$image_repo:${release}-amd64"
docker buildx imagetools inspect "$image_repo:$release"
```

Individual platform manifests are pushed explicitly because GHCR rejected the
original Docker push containing its provenance/index combination. The platform
images and the combined ARM64/AMD64 index were accepted.

Confirm both platforms and the package's private visibility before distributing
a release. Record the combined and individual digests in `release.lock`; update
`image.txt`, `images.env` and the source-information snapshot as appropriate.

## Package and publish the ZIP

```sh
./script/overleaf-package --output dist/overleaf-personal-2026-10-27.zip
```

The packager defaults to the image in `release.lock`, validates the patch
checksum, and copies an explicit allowlist. The ZIP's README comes from
`docs/BUNDLE-README.md`. It excludes `.env`, credentials, build checkouts,
container data and user projects. It includes a checksum manifest and preserves
the executable permissions of the launchers. The output file must not already
exist. An explicit `--image` digest can be supplied for validation builds.

Record the ZIP checksum and size in `release.lock`. Commit the release sources,
then create a GitHub Release for that commit with the ZIP attached. Avoid
publishing image layers or container data in Git.

## Existing installations

Pulling repository updates preserves the ignored `.env` file and Docker volumes.
The saved `.env` still selects the previous image pins. Review a new release,
stop Overleaf, update the image references in `.env`, then start it again. Retain
the invite-token secret, Compose project name and data volumes.

The earlier public `suckerpunch/overleaf-ce-arm64` Docker Hub image remains a
separate publication; this repository and its GHCR package are private.
