.PHONY: all init buildjs servejs

all: buildjs

init:
	pip install -e .
	cd frontend/ && yarn install

justjs:
	cd frontend/ && NODE_ENV=production yarn parcel build -d ../sup/static/ index.html

buildjs: init justjs

servejs:
	mkdir -p /tmp/supjs
	cd frontend/ && NODE_ENV=development yarn parcel serve --host 0.0.0.0 -d /tmp/supjs index.html
