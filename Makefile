.PHONY: all buildjs servejs

all:
	cd frontend/ && /opt/conda/envs/sup/bin/npm install
	sudo /opt/conda/envs/sup/bin/pip install .
	sudo chown -R $(USER):magaox-dev ./
	sudo chmod -R g+rwX ./

justjs:
	cd frontend/ && npx vite build --emptyOutDir --outDir ../sup/static/

servejs:
	cd frontend/ && npx vite dev --host 0.0.0.0