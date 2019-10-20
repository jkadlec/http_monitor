check:
	mypy .
	flake8 --max-line-length=120

build:
	docker-compose build

run_stdin: build
	docker run -e DISPLAY_STATS=${DISPLAY_STATS} -e INPUT_FILE='-' -i --rm datadog/processor
