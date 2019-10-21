from os import getenv


class Config(object):
    STATS_TIMESPAN = 10
    HIGH_TRAFFIC_TIMESPAN = 2 * 60  # 2 minutes
    HIGH_TRAFFIC_THRESHOLD = int(getenv('HIGH_TRAFFIC_THRESHOLD', '10'))
    DISPLAY_STATS = getenv('DISPLAY_STATS', 'true') == 'true'
    SORT_BATCH_SIZE = 128
    BATCH_USE_CHUNK = 0.6  # 0.82 + 128 is the last combination working with the input file
    STATS_TIMESPAN = 10
