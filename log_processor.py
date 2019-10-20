from collections import Counter
from enum import Enum
from typing import Tuple, List


class Actions(Enum):
    NO_OP = 1
    STATS = 2
    ALERT = 3
    ERROR = 4


class Entry(object):
    def __init__(self: 'Entry', remotehost: str, rfc931: str, authuser: str, date: str,
                 request: str, status: str, byte_count: str):
        self.remotehost = remotehost
        self.rfc931 = rfc931
        self.authuser = authuser
        self.date = int(date)
        self.request = request  # <METHOD> <PATH>
        self.status_code = int(status)
        self.byte_count = int(byte_count)

    @classmethod
    def from_str(cls, entry: str) -> 'Entry':
        return cls(*entry.split(','))


def _create_stats_output(time_from: int, time_to: int, entry_count: int,
                         sections_report: str, request_size_report: str, status_codes_report: str) -> str:
    def section_header(section: str) -> str: return f'=={section}' + '=' * (len(header) - len(f'=={section}'))
    header = f'stats from {time_from} to {time_to} ({entry_count}) entries'
    delimiter = '=' * len(header)
    return f'''\
{delimiter}\n\
{header}\n\
{section_header('request size')}\n{request_size_report}\n\
{section_header('status codes')}\n{status_codes_report}\n\
{section_header('section accesses')}\n{sections_report}\n\
{delimiter}'''


class LogProcessor(object):
    def __init__(self: 'LogProcessor', high_traffic_timespan: int, high_traffic_threshold: int):
        self.high_traffic_first_timestamp = 0
        self.high_traffic_timespan = high_traffic_timespan
        self.high_traffic_threshold = high_traffic_threshold

        self.stats_timespan = 10
        self.stats_last_returned = -1
        self.stats_first_timestamp = 0
        self.stats_timespan_msgs: List['Entry'] = []

    def _section_report(self) -> str:
        # section is /api -> api /api/something -> api as well
        def request_to_section(request: str) -> str: return request.split()[1].split('/')[1]
        def request_to_method(request: str) -> str: return request.split()[0][1:]

        section_counter = Counter(request_to_section(entry.request) for entry in self.stats_timespan_msgs)
        section_report = '\n'.join((f'section: {sec}, hits: {hits}' for sec, hits in section_counter.most_common()))

        method_counter = Counter(request_to_method(entry.request) for entry in self.stats_timespan_msgs)
        method_report = '\n'.join((f'method: {method}, hits: {hits}' for method, hits in method_counter.most_common()))

        return '\n'.join([section_report, method_report])

    def _add_entry(self, entry: 'Entry') -> Tuple['Actions', str]:
        timestamp = entry.date
        first_entry = self.stats_last_returned == -1
        if first_entry:
            self.stats_last_returned = timestamp
            self.stats_timespan_msgs.append(entry)
            return Actions.NO_OP, ''

        should_return_stats_entry_not_included = timestamp - self.stats_last_returned > self.stats_timespan
        should_return_stats_entry_included = timestamp - self.stats_last_returned == self.stats_timespan
        do_stats = should_return_stats_entry_not_included or should_return_stats_entry_included

        if should_return_stats_entry_included or not do_stats:
            self.stats_timespan_msgs.append(entry)

        if not do_stats:
            return Actions.NO_OP, ''

        # Generate stats from the last used timestamp.
        stats_from = self.stats_last_returned

        # Update stats timestamp.
        self.stats_last_returned = timestamp
        memory = self.stats_timespan_msgs
        entry_count = len(memory)

        # Generate stat strings.
        sections_report = self._section_report()
        total_bytes_count = sum(e.byte_count for e in memory)
        request_size_report = f'{total_bytes_count}B, {total_bytes_count // 1024}kB'
        status_codes_counter = Counter(e.status_code for e in memory)
        status_codes_report = '\n'.join(f'code: {code}, count: {count}'
                                        for code, count in status_codes_counter.most_common())

        self.stats_timespan_msgs = []
        return Actions.STATS, _create_stats_output(stats_from, timestamp, entry_count,
                                                   sections_report, request_size_report, status_codes_report)

    def next_entry(self: 'LogProcessor', incoming_entry: str) -> Tuple['Actions', str]:
        try:
            entry = Entry.from_str(incoming_entry)
        except Exception as e:
            return Actions.ERROR, 'Cannot parse {incoming_entry}: ' + str(e)

        action, detail = self._add_entry(entry)

        return action, detail
