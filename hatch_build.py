"""Build the Vue frontend into ``sup/static/`` as part of the Python build.

``sup/static/`` is not checked in; it is produced by ``npm run build`` in
``frontend/``, which in turn depends on ``viewarr/pkg/`` -- the wasm-pack
output of the ``viewarr`` submodule. This hook runs both steps whenever a
wheel (or an editable install) is built, so ``uv build`` / ``uv pip install .``
produce a complete package the way the old ``setup.py`` ``build_py`` subclass
did.

Build-time prerequisites: node/npm, and (only when ``viewarr/pkg/`` is absent)
a Rust toolchain with wasm-pack.

Set ``SUP_SKIP_NPM_BUILD=1`` to reuse whatever is already in ``sup/static/``
(useful on machines without node, or when iterating on the Python side).
"""

import os
import shutil
import subprocess
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

HERE = Path(__file__).parent
FRONTEND_DIR = HERE / "frontend"
STATIC_DIR = HERE / "sup" / "static"
VIEWARR_DIR = HERE / "viewarr"
VIEWARR_PKG = VIEWARR_DIR / "pkg"


class NpmBuildHook(BuildHookInterface):
    PLUGIN_NAME = "npm"

    def initialize(self, version, build_data):
        if os.environ.get("SUP_SKIP_NPM_BUILD"):
            self.app.display_warning(
                f"SUP_SKIP_NPM_BUILD set, packaging {STATIC_DIR} as-is"
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

    def _build_viewarr(self, npm):
        """Build the viewarr wasm module the frontend imports, if needed.

        frontend/package.json depends on ``file:../viewarr/pkg``, which only
        exists once wasm-pack has run. Rebuilding it on every Python build
        would be slow, so only do it when it is missing.
        """
        if (VIEWARR_PKG / "wrapper.js").exists():
            return

        if not (VIEWARR_DIR / "Cargo.toml").exists():
            raise RuntimeError(
                f"{VIEWARR_DIR} is empty. Run `git submodule update --init` "
                "to check out the viewarr submodule."
            )

        if shutil.which("wasm-pack") is None:
            raise RuntimeError(
                "viewarr/pkg/ is missing and wasm-pack was not found on PATH. "
                "Install a Rust toolchain and wasm-pack "
                "(https://rustwasm.github.io/wasm-pack/installer/), or build "
                "viewarr separately and re-run."
            )

        self.app.display_info("viewarr: npm run build (wasm-pack)")
        subprocess.run([npm, "run", "build"], cwd=VIEWARR_DIR, check=True)
