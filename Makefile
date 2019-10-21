DISPLAY_STATS ?= true
HIGH_TRAFFIC_THRESHOLD ?= 10

check:
	mypy .
	flake8 --max-line-length=120

test:
	docker build -t datadog/processor_tests -f test.Dockerfile .
	docker run -i --rm datadog/processor_tests


build:
	docker-compose build

run_stdin: build
	docker run -e DISPLAY_STATS=$(DISPLAY_STATS) -e HIGH_TRAFFIC_THRESHOLD=$(HIGH_TRAFFIC_THRESHOLD) -e INPUT_FILE='-' -i --rm datadog/processor

cleanup:
	docker rmi datadog/processor_tests datadog/processor
