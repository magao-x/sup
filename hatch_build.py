"""Build the Vue frontend into ``sup/static/`` as part of the Python build.

``sup/static/`` is not checked in; it is produced by ``npm run build`` in
``frontend/``, which in turn depends on ``viewarr-workspace/viewarr/pkg/`` --
the wasm-pack output of the viewarr library inside the ``viewarr-workspace``
submodule. This hook runs both steps whenever a wheel (or an editable install)
is built, so ``uv build`` / ``uv pip install .`` produce a complete package the
way the old ``setup.py`` ``build_py`` subclass did.

Build-time prerequisites: node/npm, and (only when the wasm-pack output is
absent) a Rust toolchain with wasm-pack.

Set ``SUP_SKIP_NPM_BUILD=1`` to reuse whatever is already in ``sup/static/``
(useful on machines without node, or when iterating on the Python side).

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
VIEWARR_PKG = VIEWARR_DIR / "pkg"


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

        self._build_viewarr(npm)

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

    def _build_viewarr(self, npm):
        """Build the viewarr wasm module the frontend imports, if needed.

        frontend/package.json depends on ``file:../viewarr-workspace/viewarr/pkg``,
        which only exists once wasm-pack has run. Rebuilding it on every Python
        build would be slow, so only do it when it is missing.
        """
        if (VIEWARR_PKG / "wrapper.js").exists():
            return

        if not (VIEWARR_DIR / "Cargo.toml").exists():
            raise RuntimeError(
                f"{VIEWARR_DIR} is empty. Run `git submodule update --init` "
                "to check out the viewarr-workspace submodule."
            )

        if shutil.which("wasm-pack") is None:
            raise RuntimeError(
                f"{VIEWARR_PKG} is missing and wasm-pack was not found on PATH. "
                "Install a Rust toolchain and wasm-pack "
                "(https://rustwasm.github.io/wasm-pack/installer/), or build "
                "viewarr separately and re-run."
            )

        self.app.display_info("viewarr: npm run build (wasm-pack)")
        subprocess.run([npm, "run", "build"], cwd=VIEWARR_DIR, check=True)
