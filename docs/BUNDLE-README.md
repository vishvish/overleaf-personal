# Your own Overleaf

This package runs an independent Overleaf Community Edition installation with
full TeX Live. Each person gets their own projects, accounts and data. The same
release supports Apple Silicon / ARM64 and Intel / AMD64; Docker selects the
appropriate image automatically.

## First use

1. Install and open OrbStack or Docker Desktop on macOS, or Docker Engine with
   Docker Compose 2.20 or newer on Linux. Windows users can run these commands
   from WSL2 with Docker Desktop integration enabled.
2. Extract the whole ZIP into a folder you will keep. Allow space for roughly
   12 GB of container images, plus your projects and Docker's build cache.
3. Open a terminal in that folder and run:

   ```sh
   ./overleaf login
   ./overleaf start
   ```

   Use your own account with permission to download the private image. The
   registry name comes from this release's `image.txt`. Registry access must
   be granted by the person sharing this release.
   For GitHub Container Registry (`ghcr.io`), enter your GitHub username and a
   [classic personal access token with `read:packages`](https://github.com/settings/tokens/new?scopes=read:packages&description=Overleaf%20image%20downloads)
   at Docker's password prompt. Your GitHub account also needs read access to
   the private package. Docker stores this login separately from the bundle.
4. Open <http://localhost:8080/launchpad> and create your own administrator
   account. For later visits, use <http://localhost:8080>.

The first download is several gigabytes. The launcher waits for Overleaf to
be ready before printing its URL. On macOS, after the initial registry sign-in,
you can double-click **Start Overleaf.command** to start it and open your browser.

## Start and stop

```sh
./overleaf start
./overleaf stop
./overleaf status
./overleaf logs
```

You can also double-click **Stop Overleaf.command** on macOS. Stopping keeps all
projects, accounts and history. Docker's automatic restart policy is disabled;
start Overleaf explicitly when you need it. Closing a browser does not stop it.

Three services stay running: Overleaf, MongoDB and Redis. A fourth container
initializes MongoDB on startup, waits for it to become writable, then exits.
MongoDB and Redis do not publish ports on your computer. The web interface
listens on `127.0.0.1:8080`, so access is local to your computer by default.

## Your configuration and data

First use creates a private `.env` file containing an installation-specific
invite-token secret. Keep that file private and retain it with your backups.
Each installation generates its own secret; this package contains no accounts
or personal project data.

Projects, the database and Redis's persistent update queue live in Docker named
volumes. The default project name is `overleaf-personal`, giving these volumes:

* `overleaf-personal_overleaf-data`
* `overleaf-personal_mongo-data`
* `overleaf-personal_redis-data`

Keep all three volumes together when backing up an installation. Stop Overleaf
first so the backup is consistent, and retain `.env`. Removing containers is
different from deleting volumes: deleting these volumes deletes your data.

If port 8080 is occupied, stop Overleaf and edit both `OVERLEAF_PORT` and
`OVERLEAF_SITE_URL` in `.env`, then start again. For example, use `8081` and
`http://localhost:8081`. For a second installation on the same Docker engine,
also choose a different `COMPOSE_PROJECT_NAME` before its first start.

This package uses the active **local** Docker context. It does not change your
Docker context or any DNS, proxy or Tailscale settings.

## LaTeX and fonts

The image includes the full TeX Live scheme and registers its font directories
with Fontconfig. Choose XeLaTeX or LuaLaTeX in Overleaf for documents using
`fontspec`. Fonts uploaded inside a project's `fonts/` folder should be loaded
by filename with `Path=fonts/`; project folders are not system font registries.

## Releases and troubleshooting

Image versions are pinned in `.env`. `./overleaf pull` downloads those exact
versions. To install a newer release, keep your `.env` and volumes and review
the release's image references before updating them; pulling alone does not
select a newer release.

If the private image cannot be downloaded, run `./overleaf login` and check that
your account has access. If startup fails, `./overleaf logs` shows the service
logs. `./overleaf config` checks the configuration without printing secrets.

This is a community-built Overleaf image. Its upstream source and build patch
are documented in `SOURCE.md`, with the upstream license in `LICENSE`.
