from sys import argv, stdin
from log_processor import LogProcessor, Actions
from config import Config as conf
from typing import IO


def _read_stream(stream: IO[str], proc: 'LogProcessor') -> None:
    # discard header
    stream.readline()
    for line in stream:
        action, output = proc.next_entry(line)
        if action == Actions.STATS:
            if conf.DISPLAY_STATS:
                print(output)
        elif action != Actions.NO_OP:
            print(output)


def main(file_path: str) -> None:
    proc = LogProcessor(high_traffic_timespan=conf.HIGH_TRAFFIC_TIMESPAN,
                        high_traffic_threshold=conf.HIGH_TRAFFIC_THRESHOLD)
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
