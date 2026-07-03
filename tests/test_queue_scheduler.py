from simulator.queue_scheduler import simulate


def test_queue_scheduler_sim_runs():
    result = simulate(
        {
            "seed": 1,
            "duration": 100,
            "total_gpus": 4,
            "workloads": 10,
            "gang_ratio": 0.2,
            "borrowing": True,
            "preemption": True,
            "quotas": {"a": 2, "b": 2},
        }
    )
    assert result["admitted"] + result["pending"] == 10

