.PHONY: all buildjs servejs

INSTALLED_PATH ?= /opt/conda/envs/sup/lib/python3.10/site-packages/sup/

all:
	cd frontend/ && /opt/conda/envs/sup/bin/npm install
	sudo /opt/conda/envs/sup/bin/pip install .
	sudo chown -R $(USER):magaox-dev ./
	sudo chmod -R g+rwX ./

justjs:
	cd frontend/ && npx vite build --emptyOutDir --outDir ../sup/static/
	sudo chown -R $(USER):magaox-dev $(INSTALLED_PATH)/static/
	sudo chmod -R g+rwX $(INSTALLED_PATH)/static/
	cp -R sup/static/* $(INSTALLED_PATH)/static/

servejs:
	cd frontend/ && npx vite dev --host 0.0.0.0