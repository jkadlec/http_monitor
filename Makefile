DISPLAY_STATS ?= true
HIGH_TRAFFIC_THRESHOLD ?= 10

install_tools:
	pip3 install mypy flake8

check: install_tools
	mypy .
	flake8 --max-line-length=120

test:
	docker build -t monitor/processor_tests -f test.Dockerfile .
	docker run -i --rm monitor/processor_tests

build:
	docker-compose build

run_stdin: build
	docker run -e DISPLAY_STATS=$(DISPLAY_STATS) -e HIGH_TRAFFIC_THRESHOLD=$(HIGH_TRAFFIC_THRESHOLD) -e INPUT_FILE='-' -i --rm monitor/processor

cleanup:
	docker rmi monitor/processor_tests monitor/processor

zip:
	git archive -o monitor.zip HEAD
