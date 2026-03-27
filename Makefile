
INSTALLED_PATH ?= "$(shell /opt/conda/envs/sup/bin/python -c 'import site;print(site.getsitepackages()[0])')/sup"

all:
	cd frontend/ && /opt/conda/envs/sup/bin/npm install
	sudo /opt/conda/envs/sup/bin/pip install --no-cache-dir .
	sudo chown -R $(USER):magaox-dev ./
	sudo chmod -R g+rwX ./

justjs:
	cd frontend/ && npx vite build --emptyOutDir --outDir ../sup/static/
	sudo chown -R $(USER):magaox-dev $(INSTALLED_PATH)/static/
	sudo chmod -R g+rwX $(INSTALLED_PATH)/static/
	cp -R sup/static/* $(INSTALLED_PATH)/static/

servejs:
	cd frontend/ && npx vite dev --host 0.0.0.0
