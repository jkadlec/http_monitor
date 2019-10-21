#! /usr/local/bin/python3

from sys import argv, stdin
from log_processor import LogProcessor, Actions
from config import Config as conf
from typing import IO, List, Tuple


def _process_line(proc: 'LogProcessor', line: str) -> None:
    actions = proc.next_entry(line)
    for action, output in actions:
        if action == Actions.STATS:
            if conf.DISPLAY_STATS:
                print(output)
        elif action != Actions.NO_OP:
            print(output)


def _time_from_line(line):
    return int(line.split(',')[3])  # Unix time is the 4th value.


def _preprocess_batch(batch) -> Tuple[List[str], List[str]]:
    '''
        Splits sorted batch into 2 batches according to config. First one is called candidate, second remainder.
        We want to process the candidate batch and the goal is to process everything in order.
        This only works because the input is relatively sorted.

        We do this by removing any entries from remainder that also exist in candidate. Our key is the timestamp.

        Example: candidate=[1, 2, 3, 4, 5], B2=[4, 5, 9, 11], result: B1=[1, 2, 3, 4, 4, 5], B2=[9, 11]
    '''

    batch_size = len(batch)
    usable_chunk_size = int(conf.BATCH_USE_CHUNK * batch_size)
    sorted_batch = sorted(batch, key=lambda _: _time_from_line(_))

    candidate_batch = sorted_batch[:usable_chunk_size]
    remainder_batch = sorted_batch[usable_chunk_size:]
    times_in_candidates = set(_time_from_line(_) for _ in candidate_batch)

    to_pop_from_remainder = set()
    for i, remainder in enumerate(remainder_batch):
        remainder_time = _time_from_line(remainder)
        if remainder_time in times_in_candidates:
            to_pop_from_remainder.add(i)

    for to_pop in to_pop_from_remainder:
        candidate_batch.append(remainder_batch[to_pop])

    remainder_batch = [_ for i, _ in enumerate(remainder_batch) if i not in to_pop_from_remainder]
    assert len(candidate_batch) + len(remainder_batch) == batch_size

    return candidate_batch, remainder_batch


def _read_stream(stream: IO[str], proc: 'LogProcessor') -> None:
    # discard header
    stream.readline()
    batch_size = conf.SORT_BATCH_SIZE
    batch = []  # We need to batch because the input is not sorted, but it's almost sorted.
    for line in stream:
        batch.append(line)
        if len(batch) == batch_size:
            to_process, batch = _preprocess_batch(batch)
            for sorted_line in to_process:
                _process_line(proc, sorted_line)

    for sorted_line in sorted(batch, key=_time_from_line):
        _process_line(proc, sorted_line)


def main(file_path: str) -> None:
    proc = LogProcessor(high_traffic_timespan=conf.HIGH_TRAFFIC_TIMESPAN,
                        high_traffic_threshold=conf.HIGH_TRAFFIC_THRESHOLD,
                        stats_timespan=conf.STATS_TIMESPAN)
    if file_path == '-':
        _read_stream(stdin, proc)
    else:
        with open(file_path) as f:
            _read_stream(f, proc)


if __name__ == '__main__':
    if len(argv) != 2:
        print(f'usage: {argv[0]} <input_file>\nUse "-" to read from stdin')
    else:
        main(argv[1])
