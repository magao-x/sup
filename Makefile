.PHONY: all init buildjs servejs

all: buildjs

init:
	pip install -e .
	cd frontend/ && yarn install

buildjs: init
	cd frontend/ && NODE_ENV=production yarn parcel build -d ../sup/static/ index.html

servejs:
	cd frontend/ && NODE_ENV=development yarn parcel serve -d ../sup/static/ index.html
