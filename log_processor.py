from collections import Counter, deque
from enum import Enum
from typing import Tuple, List, Deque, Union


class Actions(Enum):
    NO_OP = 1
    STATS = 2
    ALERT_RAISED = 3
    ALERT_CANCELLED = 4
    ERROR = 5


class Entry(object):
    def __init__(self: 'Entry', remotehost: str, rfc931: str, authuser: str, date: str,
                 request: str, status: str, byte_count: str):
        self.remotehost = remotehost.replace('"', '')
        self.rfc931 = rfc931.replace('"', '')
        self.authuser = authuser.replace('"', '')
        self.date = int(date)
        self.request = request.replace('"', '')  # <METHOD> <PATH>
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
    def __init__(self: 'LogProcessor', high_traffic_timespan: int, high_traffic_threshold: int,
                 stats_timespan: int) -> None:
        self.high_traffic_timespan = high_traffic_timespan  # seconds
        self.high_traffic_threshold = high_traffic_threshold  # requests count
        self.high_traffic_sliding_window: Deque[int] = deque()  # per second counts
        self.high_traffic_request_sum = 0
        self.high_traffic_last_second_count = 0
        self.high_traffic_alert_active: Union[bool, int] = False  # Will hold the timestamp when the alert started.

        self.last_seen_second = -1

        self.stats_timespan = stats_timespan
        self.stats_last_returned = -1
        self.stats_first_timestamp = 0
        self.stats_timespan_msgs: List['Entry'] = []

    def _section_report(self) -> str:
        # section is /api -> api /api/something -> api as well
        def request_to_section(request: str) -> str: return request.split()[1].split('/')[1]
        def request_to_method(request: str) -> str: return request.split()[0]

        section_counter = Counter(request_to_section(entry.request) for entry in self.stats_timespan_msgs)
        section_report = '\n'.join((f'section: {sec}, hits: {hits}' for sec, hits in section_counter.most_common()))

        method_counter = Counter(request_to_method(entry.request) for entry in self.stats_timespan_msgs)
        method_report = '\n'.join((f'method: {method}, hits: {hits}' for method, hits in method_counter.most_common()))

        return '\n'.join([section_report, method_report])

    def _generate_stats(self) -> Tuple['Actions', 'str']:
        timestamp = self.last_seen_second
        # Generate stats from the last used timestamp.
        stats_from = self.stats_last_returned + 1

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

    def _handle_high_traffic(self) -> Tuple['Actions', 'str']:
        window_full = len(self.high_traffic_sliding_window) == self.high_traffic_timespan
        assert len(self.high_traffic_sliding_window) <= self.high_traffic_timespan

        # Remove count from window if full.
        to_decrease = self.high_traffic_sliding_window.popleft() if window_full else 0
        to_increase = self.high_traffic_last_second_count

        if self.last_seen_second == -1:
            # Nothing else to do, this is just the init step.
            return Actions.NO_OP, ''
        else:
            # Extend window. TODO: will only work with consecutive times. Otherwise we'd have add zeros in the q.
            self.high_traffic_sliding_window.append(self.high_traffic_last_second_count)

        trigger_second = self.last_seen_second

        self.high_traffic_request_sum -= to_decrease
        self.high_traffic_request_sum += to_increase

        avg_request_count = self.high_traffic_request_sum / self.high_traffic_timespan
        over_threshold = avg_request_count > self.high_traffic_threshold

        if self.high_traffic_alert_active and not over_threshold:
            alert_origin_timestamp = self.high_traffic_alert_active
            self.high_traffic_alert_active = False
            return Actions.ALERT_CANCELLED,\
                f'{trigger_second}: high load alert: from {alert_origin_timestamp} canceled.'

        if not self.high_traffic_alert_active and over_threshold:
            self.high_traffic_alert_active = trigger_second
            return Actions.ALERT_RAISED, f'{trigger_second} high load alert: {avg_request_count} requests \
over the last {self.high_traffic_timespan} seconds on average.'

        return Actions.NO_OP, ''

    def _add_entry(self, entry: 'Entry') -> Tuple[Tuple['Actions', str], Tuple['Actions', str]]:
        timestamp = entry.date
        assert timestamp >= self.last_seen_second  # TODO: This relies on preprocessing and can fail.
        if self.last_seen_second == -1:
            self.last_seen_second = timestamp

        if self.last_seen_second == timestamp:
            # Extend this second counter and stats memory, take no other action at this stage.
            self.high_traffic_last_second_count += 1
            self.stats_timespan_msgs.append(entry)

            first_stats_entry = self.stats_last_returned == -1
            if first_stats_entry:
                self.stats_last_returned = timestamp - 1  # We need to include this entry's time as well.
            return ((Actions.NO_OP, ''), (Actions.NO_OP, ''))

        # We've seen all the data for the previous second.
        should_return_stats = self.last_seen_second - (self.stats_last_returned + 1) >= self.stats_timespan
        stats_action = (Actions.NO_OP, '')
        if should_return_stats and self.stats_last_returned != -1:
            stats = self._generate_stats()
            stats_action = stats

        high_traffic_action = self._handle_high_traffic()

        # Init high traffic counter with new second.
        self.high_traffic_last_second_count = 1
        self.last_seen_second = entry.date

        # Update stats memory
        self.stats_timespan_msgs.append(entry)

        return (stats_action, high_traffic_action)

    def next_entry(self: 'LogProcessor', incoming_entry: str) -> Tuple[Tuple['Actions', str], Tuple['Actions', str]]:
        try:
            entry = Entry.from_str(incoming_entry)
        except Exception as e:
            return ((Actions.ERROR, 'Cannot parse {incoming_entry}: ' + str(e)), (Actions.NO_OP, ''))

        actions = self._add_entry(entry)

        return actions
