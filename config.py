from os import getenv


class Config(object):
    STATS_TIMESPAN = 10
    HIGH_TRAFFIC_TIMESPAN = 2 * 60  # 2 minutes
    HIGH_TRAFFIC_THRESHOLD = int(getenv('HIGH_TRAFFIC_THRESHOLD', '10'))
    DISPLAY_STATS = getenv('DISPLAY_STATS', 'true') == 'true'
