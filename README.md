# Your own Overleaf

A turnkey Overleaf Community Edition setup for independent personal
installations. The application image includes full TeX Live and supports Apple
Silicon / ARM64 and Intel / AMD64. A launcher manages Overleaf, MongoDB and Redis
as one Docker Compose application.

Each installation creates its own administrator account, project storage and
private configuration. The source and
[container image](https://github.com/users/vishvish/packages/container/package/overleaf-personal)
are public. No GitHub account, token or registry login is required to run it.

## Start

Install and open OrbStack or Docker Desktop on macOS, or Docker Engine with
Compose 2.20 or newer on Linux. Windows users can use WSL2 with Docker Desktop
integration. Then download the ZIP from [Releases](https://github.com/vishvish/overleaf-personal/releases)
or clone the repository:

```sh
git clone https://github.com/vishvish/overleaf-personal.git
cd overleaf-personal
./overleaf start
```

Docker downloads the public images automatically. See the
[installation guide](docs/BUNDLE-README.md) for full requirements and configuration.

On first use, open <http://localhost:8080/launchpad> to create your administrator
account. Later visits use <http://localhost:8080>. The first image download is
several gigabytes.

## Stop and return later

```sh
./overleaf stop
./overleaf start
```

On macOS, the included **Start Overleaf.command**
and **Stop Overleaf.command** files provide the same operations from Finder.
Use `./overleaf status` or `./overleaf logs` for diagnostics.

The application listens on localhost by default. Projects and accounts persist
in three Docker named volumes, while first use generates a private `.env` file.
Keep `.env` and all three data volumes together for backups. Docker automatic
restart is disabled, so start Overleaf when you need it.

## What's here

* `overleaf`, `compose.yaml` and `mongo-init.js`: installation and lifecycle.
* `image.txt`, `images.env` and `release.lock`: pinned application and database images.
* `SOURCE.md`, `texlive-full.patch` and `LICENSE`: upstream source and build information.
* `script/overleaf-package`: creates the small ZIP distributed through Releases.
* `tests/` and the GitHub Actions workflow: configuration and packaging checks.

The [maintainer guide](docs/MAINTAINING.md) covers rebuilding both image variants,
publishing a combined GHCR release and generating the ZIP.

## Checks

Python 3 and Bash are sufficient for the repository checks:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

The current image was checked with native ARM64 startup, data persistence and
non-root XeLaTeX compilation. AMD64 startup and compilation were checked under
OrbStack emulation. Physical Intel and friends' fresh-machine tests remain
unverified. The fast CI checks do not start Docker or rebuild TeX Live.

This is a community-built Overleaf image. Upstream source and licensing are
documented in [SOURCE.md](SOURCE.md) and [LICENSE](LICENSE).
