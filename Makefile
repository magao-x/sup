.PHONY: all init buildjs servejs

all: buildjs

init:
	pip install -e .
	cd frontend/ && yarn install

justjs:
	cd frontend/ && NODE_ENV=production yarn parcel build -d ../sup/static/ index.html
	cd frontend/ && NODE_ENV=production yarn parcel build -d ../sup/static/ video.html

buildjs: init justjs

servejs:
	mkdir -p /tmp/supjs
	cd frontend/ && NODE_ENV=development yarn parcel serve -d /tmp/supjs index.html
