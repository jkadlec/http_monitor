from sys import argv, stdin
from log_processor import LogProcessor
from config import Config
from typing import IO


def _read_stream(stream: IO[str], proc: 'LogProcessor') -> None:
    # discard header
    stream.readline()
    for line in stream:
        _, output = proc.next_entry(line)
        if any(output):
            print(output)


def main(file_path: str) -> None:
    proc = LogProcessor(high_traffic_timespan=Config.HIGH_TRAFFIC_TIMESPAN,
                        high_traffic_threshold=Config.HIGH_TRAFFIC_THRESHOLD)
    if file_path == '-':
        _read_stream(stdin, proc)
    else:
        with open(file_path) as f:
            _read_stream(f, proc)


if __name__ == '__main__':
    if len(argv) != 2:
        print('usage: ./{argv[0]} <input_file>\nUse "-" to read from stdin')
    else:
        main(argv[1])
