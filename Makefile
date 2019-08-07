.PHONY: all init buildjs

init:
	yarn install
	pip install -e .

buildjs:
	yarn parcel build -d sup/static/ frontend/index.html

all: init buildjs

serve:
	yarn parcel watch -d sup/static/ frontend/index.html &
	sup
