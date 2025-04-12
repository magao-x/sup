.PHONY: all init buildjs servejs

all: buildjs

init:
	sudo /opt/conda/envs/sup/bin/pip install .
	sudo chown -R $(USER):magaox-dev ./
	sudo chmod -R g+rwX ./
	cd frontend/ && /opt/conda/envs/sup/bin/yarn install

justjs:
	cd frontend/ && NODE_ENV=production yarn parcel build -d ../sup/static/ index.html

buildjs: init justjs

servejs:
	mkdir -p /tmp/supjs
	cd frontend/ && NODE_ENV=development yarn parcel serve --host 0.0.0.0 -d /tmp/supjs index.html
