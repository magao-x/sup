"""Build the Vue frontend into ``sup/static/`` as part of the Python build.

``sup/static/`` is not checked in; it is produced by ``npm run build`` in
``frontend/``, which in turn depends on the wasm-pack output (``pkg/``) of
three packages inside the ``viewarr-workspace`` submodule: the viewarr
library, the viewcam camera viewer, and viewcam-codec's frame decoder. This hook runs both steps whenever a wheel (or an editable install)
is built, so ``uv build`` / ``uv pip install .`` produce a complete package the
way the old ``setup.py`` ``build_py`` subclass did.

Build-time prerequisites: node/npm, and a Rust toolchain with wasm-pack to
rebuild those packages. Without wasm-pack the build falls back to whatever is
already in their ``pkg/`` directories, warning that it may be stale; if
nothing is there to fall back to, it is an error.

Set ``SUP_SKIP_NPM_BUILD=1`` to reuse whatever is already in ``sup/static/``
(useful on machines without node, or when iterating on the Python side), or
``SUP_SKIP_VIEWARR_BUILD=1`` to rebuild the frontend against the existing
``pkg/`` directories without paying for wasm-pack.

Building a wheel *from an sdist* takes that same path automatically: the sdist
carries a built ``sup/static/`` but not the viewarr submodule, so there is
nothing to rebuild from and the prebuilt assets are used as they are.
"""

import os
import shutil
import subprocess
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

HERE = Path(__file__).parent
GIT_DIR = HERE / ".git"
FRONTEND_DIR = HERE / "frontend"
STATIC_DIR = HERE / "sup" / "static"
# The submodule is the whole viewarr workspace (the library plus its other
# downstream consumers); the library sup builds against is one directory in.
WORKSPACE_DIR = HERE / "viewarr-workspace"
VIEWARR_DIR = WORKSPACE_DIR / "viewarr"
# The submodule's WASM packages the frontend imports, each with a file its
# build leaves in pkg/.
WASM_PACKAGES = {
    "viewarr": (VIEWARR_DIR, "wrapper.js"),
    "viewcam": (WORKSPACE_DIR / "viewcam", "wrapper.js"),
    "viewcam-codec": (WORKSPACE_DIR / "viewcam-codec", "viewcam_codec.js"),
}


class NpmBuildHook(BuildHookInterface):
    PLUGIN_NAME = "npm"

    def initialize(self, version, build_data):
        if os.environ.get("SUP_SKIP_NPM_BUILD"):
            self.app.display_warning(
                f"SUP_SKIP_NPM_BUILD set, packaging {STATIC_DIR} as-is"
            )
            return

        if self._is_sdist_build():
            self.app.display_info(
                f"building from an sdist, packaging {STATIC_DIR} as built"
            )
            if not (STATIC_DIR / "index.html").exists():
                raise RuntimeError(
                    f"{STATIC_DIR} is missing from this sdist, and the viewarr "
                    "sources needed to rebuild it are not part of one. Build "
                    "from a git checkout instead."
                )
            return

        npm = os.environ.get("NPM", shutil.which("npm"))
        if npm is None:
            raise RuntimeError(
                "npm was not found on PATH. Install node, point $NPM at an npm "
                "executable, or set SUP_SKIP_NPM_BUILD=1 to package the "
                "existing sup/static/ directory."
            )

        for name, (package_dir, built_file) in WASM_PACKAGES.items():
            self._build_wasm_package(npm, name, package_dir, built_file)

        for command in (["install"], ["run", "build"]):
            self.app.display_info(f"frontend: npm {' '.join(command)}")
            subprocess.run([npm, *command], cwd=FRONTEND_DIR, check=True)

        if not (STATIC_DIR / "index.html").exists():
            raise RuntimeError(f"frontend build did not populate {STATIC_DIR}")

    def _is_sdist_build(self):
        """Is this a wheel being built from an unpacked sdist?

        An sdist has no ``.git``, and cannot carry the viewarr sources: the
        workspace reaches its library through symlinks, and the packaging
        machinery resolves those to the one real directory and records it
        only once, under a symlinked path. Rather than depend on which copy
        survives, sdists ship the already-built ``sup/static/`` and wheels
        built from them reuse it.
        """
        return not GIT_DIR.exists() and not (VIEWARR_DIR / "Cargo.toml").exists()

    def _build_wasm_package(self, npm, name, package_dir, built_file):
        """Rebuild one of the wasm modules the frontend imports.

        frontend/package.json depends on e.g. ``file:../viewarr-workspace/viewarr/pkg``,
        which only exists once wasm-pack has run. The submodule checkout it is
        built from moves -- a bump, a branch switch -- and a ``pkg/`` left over
        from the previous one is invisible: the frontend bundles it, the build
        succeeds, and the install quietly ships the old viewer. So rebuild
        unconditionally and let cargo's own caching keep the no-op case cheap,
        rather than trusting the output's mere existence to mean it is current.
        """
        pkg = package_dir / "pkg"
        have_pkg = (pkg / built_file).exists()

        if not (package_dir / "Cargo.toml").exists():
            raise RuntimeError(
                f"{package_dir} is empty. Run `git submodule update --init` "
                "to check out the viewarr-workspace submodule."
            )

        if os.environ.get("SUP_SKIP_VIEWARR_BUILD"):
            if not have_pkg:
                raise RuntimeError(
                    f"SUP_SKIP_VIEWARR_BUILD is set but {pkg} does not "
                    "exist, so the frontend has nothing to build against. "
                    f"Unset it to build {name}."
                )
            self.app.display_warning(
                f"SUP_SKIP_VIEWARR_BUILD set, reusing {pkg} "
                f"(it may not match the current {name} checkout)"
            )
            return

        if shutil.which("wasm-pack") is None:
            if not have_pkg:
                raise RuntimeError(
                    f"{pkg} is missing and wasm-pack was not found on "
                    "PATH. Install a Rust toolchain and wasm-pack "
                    "(https://rustwasm.github.io/wasm-pack/installer/), or "
                    f"build {name} separately and re-run."
                )
            self.app.display_warning(
                f"wasm-pack was not found on PATH, so {pkg} cannot be "
                "rebuilt; reusing it as-is. It may not match the current "
                f"{name} checkout, in which case this build will ship an "
                "out-of-date copy."
            )
            return

        self.app.display_info(f"{name}: npm run build (wasm-pack)")
        subprocess.run([npm, "run", "build"], cwd=package_dir, check=True)
