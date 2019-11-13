.PHONY: all init buildjs servejs

init:
	yarn install
	pip install -e .

buildjs:
	cd frontend/ && NODE_ENV=development yarn parcel build -d ../sup/static/ index.html

all: init buildjs

servejs:
	cd frontend/ && yarn parcel serve -d ../sup/static/ index.html

