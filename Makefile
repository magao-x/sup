.PHONY: all init buildjs servejs

all: buildjs

init:
	pip install -e .
	cd frontend/ && yarn install

buildjs: init
	cd frontend/ && yarn parcel build -d ../sup/static/ index.html


servejs: init
	cd frontend/ && yarn parcel serve -d ../sup/static/ index.html
