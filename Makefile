
SUP_ENV ?= /opt/conda/envs/sup
SUP_PYTHON := $(SUP_ENV)/bin/python
INSTALLED_PATH ?= "$(shell $(SUP_PYTHON) -c 'import site;print(site.getsitepackages()[0])')/sup"

all: wheel install

# Build a wheel into dist/ as yourself. This is where all the work happens --
# the build hook (hatch_build.py) runs wasm-pack for viewarr and npm for the
# frontend -- so it needs your Rust toolchain and the sup env's npm, neither
# of which root has. Do not run it under sudo.
wheel:
	rm -f dist/sup-*.whl
	PATH="$(SUP_ENV)/bin:$(PATH)" $(SUP_PYTHON) -m pip wheel --no-deps --wheel-dir dist/ .

# Install the wheel from `make wheel` into the shared env as root. Installing
# a wheel runs no build step, so root needs nothing but the env's pip.
# Deliberately not dependent on `wheel`, so `sudo make install` cannot end up
# building as root. The second pip run is because pip skips a wheel whose
# version is already installed, and a rebuild usually does not bump it; the
# first one is still needed to pick up any new dependencies.
install:
	@ls dist/sup-*.whl >/dev/null 2>&1 || { echo "no wheel in dist/, run 'make wheel' first" >&2; exit 1; }
	sudo $(SUP_PYTHON) -m pip install --no-cache-dir dist/sup-*.whl
	sudo $(SUP_PYTHON) -m pip install --no-cache-dir --no-deps --force-reinstall dist/sup-*.whl

# frontend/ imports viewarr from viewarr-workspace/viewarr/pkg/, the wasm-pack
# output. Nothing else rebuilds it, and a pkg/ left over from a different
# submodule checkout is invisible -- vite bundles it and the viewer silently
# stays on the old code -- so rebuild it here. cargo no-ops when it is current.
viewarr:
	cd viewarr-workspace/viewarr/ && npm run build

# Build the frontend into sup/static/ in this checkout. Needs no root, and
# touches nothing outside the working tree -- enough on its own when sup runs
# from the checkout (an editable install) rather than from site-packages.
justjs: viewarr
	cd frontend/ && npx vite build --emptyOutDir --outDir ../sup/static/

# Publish an already-built sup/static/ over the installed copy: run `make
# justjs` first. Deliberately not a prerequisite of this target -- this is the
# half that needs root, and under `sudo make installjs` a prerequisite would
# build as root, whose PATH has neither wasm-pack nor the conda npm.
installjs:
	sudo chown -R $(USER):magaox-dev $(INSTALLED_PATH)/static/
	sudo chmod -R g+rwX $(INSTALLED_PATH)/static/
	cp -R sup/static/* $(INSTALLED_PATH)/static/

servejs:
	cd frontend/ && npx vite dev --host 0.0.0.0

test:
	uv run pytest
	cd frontend/ && npx playwright test

test-browser:
	cd frontend/ && npx playwright test

fake-audible-alerts:
	uv run python tests/fake_audible_alerts_device.py

.PHONY: all wheel install viewarr justjs installjs test test-browser fake-audible-alerts
