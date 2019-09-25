.PHONY: all init buildjs

init:
	yarn install
	pip install -e .

buildjs:
	NODE_ENV=development yarn parcel build -d sup/static/ frontend/index.html

all: init buildjs

serve:
	NODE_ENV=development yarn parcel watch -d sup/static/ frontend/index.html &
	sup
