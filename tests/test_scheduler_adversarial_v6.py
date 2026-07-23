from __future__ import annotations

from datetime import datetime, timedelta, timezone

from valideval.execution.shards import heartbeat_is_stale, plan_worker_assignments


def test_lpt_scheduler_is_deterministic_and_balances_long_jobs():
    tasks = [
        {"task_id": "small-a", "estimated_duration": 1},
        {"task_id": "large", "estimated_duration": 10},
        {"task_id": "small-b", "estimated_duration": 1},
        {"task_id": "medium", "estimated_duration": 5},
    ]
    first = plan_worker_assignments(tasks, gpu_ids=("0", "1"))
    second = plan_worker_assignments(list(reversed(tasks)), gpu_ids=("0", "1"))
    assert first == second
    assert first[0].task_ids[0] == "large"
    assert first[1].task_ids[0] == "medium"


def test_stale_heartbeat_fails_closed():
    now = datetime.now(timezone.utc)
    assert heartbeat_is_stale(
        {"heartbeat": (now - timedelta(minutes=10)).isoformat()},
        now=now,
        stale_after_seconds=60,
    )
    assert not heartbeat_is_stale(
        {"heartbeat": now.isoformat()},
        now=now,
        stale_after_seconds=60,
    )
    assert heartbeat_is_stale({"heartbeat": "not-a-time"}, now=now)
