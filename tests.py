from log_processor import LogProcessor, Actions


def _check_actions(actions, stats_action, traffic_action):
    return actions[0][0] == stats_action and actions[1][0] == traffic_action


def test_alert():
    proc = LogProcessor(high_traffic_timespan=2, high_traffic_threshold=2, stats_timespan=1000)

    # second 1
    for _ in range(3):
        actions = proc.next_entry('"10.0.0.2","-","apache",1,"GET /api/user HTTP/1.0",200,1234')
    assert _check_actions(actions, Actions.NO_OP, Actions.NO_OP)
    # second 2
    for _ in range(3):
        actions = proc.next_entry('"10.0.0.2","-","apache",2,"GET /api/user HTTP/1.0",200,1234')
    assert _check_actions(actions, Actions.NO_OP, Actions.NO_OP)

    # second 3 introduced, alert should be returned.
    actions = proc.next_entry('"10.0.0.2","-","apache",3,"GET /api/user HTTP/1.0",200,1234')  # avg = (3 + 3) / 2 = 3.0
    assert _check_actions(actions, Actions.NO_OP, Actions.ALERT_RAISED)

    # 1 more second of just 1 rps, alert should be cancelled.
    actions = proc.next_entry('"10.0.0.2","-","apache",4,"GET /api/user HTTP/1.0",200,1234')  # avg = (3 + 1) / 2 = 2.0
    assert _check_actions(actions, Actions.NO_OP, Actions.ALERT_CANCELLED)
