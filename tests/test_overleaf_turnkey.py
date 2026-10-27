"""Check release isolation and preservation of installation credentials."""

import hashlib
import os
from pathlib import Path
import stat
import subprocess
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
IMAGE = "example.invalid/friends/overleaf@sha256:" + "a" * 64


class TurnkeyReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="overleaf-package-test-")
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.archive = self.directory / "release.zip"
        subprocess.run([str(ROOT / "script/overleaf-package"), "--image", IMAGE,
                        "--output", str(self.archive)], check=True, capture_output=True)
        self.bundle = self.unpack("first")
        self.environment = {key: value for key, value in os.environ.items()
                            if not key.startswith(("OVERLEAF_", "COMPOSE_"))}

    def unpack(self, name):
        destination = self.directory / name
        with zipfile.ZipFile(self.archive) as archive:
            archive.extractall(destination)
        bundle = destination / "overleaf-personal"
        # Python's extractall does not restore Unix executable mode.
        (bundle / "overleaf").chmod(0o755)
        return bundle

    def setup_bundle(self, bundle=None, **environment):
        return subprocess.run(["/bin/bash", str((bundle or self.bundle) / "overleaf"), "setup"],
                              env={**self.environment, **environment},
                              capture_output=True, text=True)

    def test_release_contains_only_distribution_files(self):
        expected = {"README.md", "compose.yaml", "mongo-init.js", "images.env",
                    "overleaf", "Start Overleaf.command", "Stop Overleaf.command",
                    "LICENSE", "image.txt", "texlive-full.patch", "SOURCE.md", "SHA256SUMS"}
        with zipfile.ZipFile(self.archive) as archive:
            self.assertEqual({Path(name).name for name in archive.namelist()}, expected)
            launcher = archive.getinfo("overleaf-personal/overleaf")
            self.assertEqual((launcher.external_attr >> 16) & 0o777, 0o755)
            self.assertEqual(archive.read("overleaf-personal/image.txt").decode().strip(), IMAGE)
        for line in (self.bundle / "SHA256SUMS").read_text().splitlines():
            digest, name = line.split("  ", 1)
            self.assertEqual(hashlib.sha256((self.bundle / name).read_bytes()).hexdigest(), digest)

    def test_checked_in_release_pins_are_consistent(self):
        lock = dict(line.split("=", 1) for line in (ROOT / "release.lock").read_text().splitlines() if "=" in line)
        images = dict(line.split("=", 1) for line in (ROOT / "images.env").read_text().splitlines() if "=" in line)
        self.assertEqual((ROOT / "image.txt").read_text().strip(), lock["IMAGE"])
        self.assertEqual(images["MONGO_IMAGE"], lock["MONGO_IMAGE"])
        self.assertEqual(images["REDIS_IMAGE"], lock["REDIS_IMAGE"])
        self.assertEqual(hashlib.sha256((ROOT / lock["PATCH"]).read_bytes()).hexdigest(), lock["PATCH_SHA256"])

    def test_first_run_generates_unique_private_configuration(self):
        result = self.setup_bundle()
        self.assertEqual(result.returncode, 0, result.stderr)
        other = self.unpack("second")
        result = self.setup_bundle(other)
        self.assertEqual(result.returncode, 0, result.stderr)
        first_text = (self.bundle / ".env").read_text()
        second_text = (other / ".env").read_text()
        first = dict(line.split("=", 1) for line in first_text.splitlines() if "=" in line)
        second = dict(line.split("=", 1) for line in second_text.splitlines() if "=" in line)
        self.assertRegex(first["OVERLEAF_INVITE_TOKEN_SECRET"], r"^[a-f0-9]{64}$")
        self.assertTrue(first["OVERLEAF_INVITE_TOKEN_SECRET"] != second["OVERLEAF_INVITE_TOKEN_SECRET"],
                        "Each installation must have its own invite secret")
        self.assertEqual(stat.S_IMODE((self.bundle / ".env").stat().st_mode), 0o600)
        self.assertEqual(first["OVERLEAF_SITE_URL"], "http://localhost:8080")
        self.assertTrue(first["OVERLEAF_INVITE_TOKEN_SECRET"] not in result.stdout)

    def test_repeated_setup_preserves_credentials_and_customizations(self):
        self.assertEqual(self.setup_bundle().returncode, 0)
        environment_file = self.bundle / ".env"
        with environment_file.open("a") as stream:
            stream.write("# Keep this installation's configuration.\n")
        before = environment_file.read_bytes()
        result = self.setup_bundle(OVERLEAF_PORT="18090")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(environment_file.read_bytes() == before, "Setup overwrote saved configuration")

    def test_setup_rejects_symlink_without_following_it(self):
        target = self.directory / "other-file"
        target.write_text("leave this alone\n")
        (self.bundle / ".env").symlink_to(target)
        result = self.setup_bundle()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(target.read_text(), "leave this alone\n")

    def test_invalid_port_does_not_create_configuration(self):
        result = self.setup_bundle(OVERLEAF_PORT="99999")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.bundle / ".env").exists())

    def test_invalid_url_cannot_inject_dotenv_values(self):
        result = self.setup_bundle(OVERLEAF_SITE_URL="http://localhost:8080\nEXTRA=1")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.bundle / ".env").exists())

    def test_start_refuses_remote_docker_before_deploying(self):
        self.assertEqual(self.setup_bundle().returncode, 0)
        binaries = self.directory / "bin"
        binaries.mkdir()
        docker = binaries / "docker"
        docker.write_text("""#!/bin/sh
case "$*" in
  'compose version --short') echo 5.6.1 ;;
  'context inspect '* ) echo ssh://unrelated-server ;;
  *) echo UNEXPECTED_DOCKER_OPERATION >&2; exit 97 ;;
esac
""")
        docker.chmod(0o755)
        environment = {**self.environment, "PATH": str(binaries) + ":" + self.environment["PATH"]}
        environment.pop("DOCKER_HOST", None)
        environment.pop("DOCKER_CONTEXT", None)
        result = subprocess.run(["/bin/bash", str(self.bundle / "overleaf"), "start"],
                                env=environment, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Select a local Docker context", result.stderr)
        self.assertNotIn("UNEXPECTED_DOCKER_OPERATION", result.stderr)

    def test_saved_installation_takes_precedence_over_other_projects_exports(self):
        self.assertEqual(self.setup_bundle().returncode, 0)
        binaries = self.directory / "bin"
        binaries.mkdir()
        docker = binaries / "docker"
        docker.write_text("""#!/bin/sh
case "$*" in
  'compose version --short') echo 5.6.1 ;;
  'context inspect '* ) echo unix:///tmp/docker.sock ;;
  'info '* ) echo linux/amd64 ;;
  'compose --project-name overleaf-personal '* )
    if test -n "${COMPOSE_PROJECT_NAME:-}${OVERLEAF_IMAGE:-}${OVERLEAF_INVITE_TOKEN_SECRET:-}"; then
      echo EXPORTED_CONFIGURATION_WAS_NOT_ISOLATED >&2
      exit 97
    fi ;;
  *) echo WRONG_PROJECT >&2; exit 98 ;;
esac
""")
        docker.chmod(0o755)
        environment = {**self.environment, "PATH": str(binaries) + ":" + self.environment["PATH"],
                       "COMPOSE_PROJECT_NAME": "another-project", "OVERLEAF_IMAGE": "another-image",
                       "OVERLEAF_INVITE_TOKEN_SECRET": "another-projects-value"}
        environment.pop("DOCKER_HOST", None)
        environment.pop("DOCKER_CONTEXT", None)
        result = subprocess.run(["/bin/bash", str(self.bundle / "overleaf"), "config"],
                                env=environment, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Configuration is valid", result.stdout)


if __name__ == "__main__":
    unittest.main()
