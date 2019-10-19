class LogProcessor(object):
    def __init__(self: 'LogProcessor', high_traffic_timespan: int, high_traffic_threshold: int):
        self.high_traffic_timespan = high_traffic_timespan
        self.high_traffic_threshold = high_traffic_threshold

    def next_entry(self: 'LogProcessor', entry: str):
        return {}, entry
