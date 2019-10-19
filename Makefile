check:
	mypy .
	flake8 --max-line-length=120

build:
	docker-compose build

run:
	docker-compose up

up:
	docker-compose up
