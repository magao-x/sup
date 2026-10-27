
INSTALLED_PATH ?= "$(shell /opt/conda/envs/sup/bin/python -c 'import site;print(site.getsitepackages()[0])')/sup"

all:
	cd frontend/ && PATH="/opt/conda/envs/sup/bin:$(PATH)" /opt/conda/envs/sup/bin/npm install
	PATH="/opt/conda/envs/sup/bin:$(PATH)" sudo -E /opt/conda/envs/sup/bin/pip install --no-cache-dir .
	sudo chown -R $(USER):magaox-dev ./
	sudo chmod -R g+rwX ./

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

.PHONY: viewarr justjs installjs test test-browser fake-audible-alerts
