.PHONY: all init buildjs servejs

init:
	pip install -e .
	cd frontend/ && yarn install

buildjs: init
	cd frontend/ && yarn parcel build -d ../sup/static/ index.html

all: buildjs

servejs: init
	cd frontend/ && yarn parcel serve -d ../sup/static/ index.html

